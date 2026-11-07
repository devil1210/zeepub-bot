# services/kofi_service.py

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from config.config_settings import config
from core.db_manager_pg import pg_manager
from models.users import User
from repositories.donation_repository import donation_repo
from repositories.user_repository import user_repo
from services.cache_service import cache_manager
from services.settings_service import get_setting
from services.tier_service import tier_service

logger = logging.getLogger(__name__)


class KofiService:
    """
    Servicio de integración para Webhooks de donaciones y suscripciones de Ko-fi.
    Procesa pagos (Donation, Subscription, Commission, Shop Order), valida tokens,
    asocia usuarios de Telegram automáticamente y actualiza sus niveles/beneficios.
    """

    def verify_token(self, token: str) -> bool:
        """
        Valida el verification_token recibido contra la configuración del bot.
        Si no se ha configurado KOFI_VERIFICATION_TOKEN en el entorno, permite
        el procesamiento pero registra una advertencia para no bloquear el inicio.
        """
        expected = config.KOFI_VERIFICATION_TOKEN or ""
        if not expected:
            logger.warning(
                "⚠️ KOFI_VERIFICATION_TOKEN no está configurado en las variables de entorno. "
                "Permitiendo solicitud de webhook sin validar token de seguridad."
            )
            return True

        return token == expected

    async def process_webhook(self, raw_data: str | dict[str, Any]) -> dict[str, Any]:
        """
        Procesa el payload completo del webhook de Ko-fi.
        Acepta tanto la cadena JSON cruda del campo 'data' (form-url-encoded)
        como un diccionario previamente parseado.
        """
        if isinstance(raw_data, str):
            try:
                payload = json.loads(raw_data)
            except Exception as e:  # noqa: BLE001
                logger.error(f"❌ Error parseando JSON de Ko-fi: {e}")
                return {"success": False, "error": "Invalid JSON payload"}
        else:
            payload = raw_data

        verification_token = payload.get("verification_token", "")
        if not self.verify_token(verification_token):
            logger.error("❌ Token de verificación de Ko-fi inválido o rechazado.")
            return {"success": False, "error": "Invalid verification token"}

        message_id = payload.get("message_id")
        if not message_id:
            logger.error("❌ Webhook de Ko-fi sin 'message_id'.")
            return {"success": False, "error": "Missing message_id"}

        # 1. Idempotencia: Verificar si ya procesamos este message_id
        existing_tx = await donation_repo.get_by_message_id(message_id)
        if existing_tx:
            logger.info(
                f"🔁 Transacción de Ko-fi {message_id} ya procesada previamente (idempotente)."
            )
            return {
                "success": True,
                "message": "Transaction already processed",
                "message_id": message_id,
                "status": existing_tx.status,
            }

        # 2. Extraer datos del pago
        tx_id = payload.get("kofi_transaction_id")
        timestamp_str = payload.get("timestamp")
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        if timestamp_str:
            try:
                # Ko-fi envía formato ISO: '2026-11-07T14:58:44Z'
                # Convertir a datetime UTC offset-naive para compatibilidad con Postgres TIMESTAMP
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                timestamp = dt.replace(tzinfo=None)
            except Exception:  # noqa: BLE001
                timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

        payment_type = payload.get("type", "Donation")
        try:
            amount = float(payload.get("amount", 0.0) or 0.0)
        except (ValueError, TypeError):
            amount = 0.0

        currency = payload.get("currency", "USD")
        from_name = payload.get("from_name") or ""
        message = payload.get("message") or ""
        email = (payload.get("email") or "").strip().lower()
        tier_name = payload.get("tier_name")
        is_subscription = bool(payload.get("is_subscription_payment", False))
        is_first_sub = bool(payload.get("is_first_subscription_payment", False))
        is_public = bool(payload.get("is_public", True))

        logger.info(
            f"☕ Recibido pago de Ko-fi: De='{from_name}', Monto={amount} {currency}, "
            f"Tipo='{payment_type}', Tier='{tier_name}', Email='{email}'"
        )

        # 3. Identificar al usuario en ZeePub
        user = await self._find_user(message=message, from_name=from_name, email=email)

        # 4. Determinar nivel a otorgar y duración
        target_tier, duration_days = await self._determine_tier_and_duration(
            amount=amount,
            tier_name=tier_name,
            is_subscription=is_subscription,
        )

        telegram_id = user.telegram_id if user else None
        display_name = (
            user.name or user.nickname or user.username if user else from_name
        )
        status = "processed" if user else "unlinked"

        # 5. Aplicar beneficios si encontramos al usuario
        if user:
            try:
                updated = await user_repo.update_user_level(
                    telegram_id=user.telegram_id,
                    level_ref=target_tier,
                    days=duration_days,
                )
                if updated:
                    await cache_manager.delete_user(user.telegram_id)
                    await tier_service.invalidate_caches()
                    logger.info(
                        f"✅ Usuario {user.telegram_id} ({display_name}) actualizado a nivel "
                        f"'{target_tier}' por {duration_days} días vía Ko-fi."
                    )
                    # Enviar mensaje de confirmación al usuario
                    await self._notify_user(
                        telegram_id=user.telegram_id,
                        display_name=display_name,
                        amount=amount,
                        currency=currency,
                        target_tier=target_tier,
                        duration_days=duration_days,
                        is_subscription=is_subscription,
                    )
                else:
                    logger.error(
                        f"❌ Falló update_user_level para telegram_id {user.telegram_id}"
                    )
                    status = "error"
            except Exception as e:  # noqa: BLE001
                logger.error(
                    f"❌ Excepción aplicando nivel a usuario {user.telegram_id}: {e}"
                )
                status = "error"
        else:
            logger.warning(
                f"⚠️ Donación de Ko-fi no vinculada automáticamente: De='{from_name}', "
                f"Email='{email}', Mensaje='{message}'. Registrada como 'unlinked'."
            )

        # 6. Registrar transacción en la base de datos
        tx_data = {
            "provider": "kofi",
            "message_id": message_id,
            "kofi_transaction_id": tx_id,
            "timestamp": timestamp,
            "payment_type": payment_type,
            "amount": amount,
            "currency": currency,
            "from_name": from_name,
            "message": message,
            "email": email,
            "tier_name": tier_name,
            "is_subscription": is_subscription,
            "is_first_subscription": is_first_sub,
            "is_public": is_public,
            "telegram_id": telegram_id,
            "user_display_name": display_name,
            "tier_granted": target_tier if user else None,
            "duration_days": duration_days if user else None,
            "status": status,
            "raw_data": payload,
        }
        await donation_repo.create_transaction(tx_data)

        # 7. Notificar a los administradores / canal de logs
        await self._notify_admins(
            from_name=from_name,
            amount=amount,
            currency=currency,
            payment_type=payment_type,
            tier_name=tier_name,
            target_tier=target_tier,
            duration_days=duration_days,
            email=email,
            message=message,
            tx_id=tx_id or message_id,
            user=user,
        )

        return {
            "success": True,
            "message_id": message_id,
            "status": status,
            "telegram_id": telegram_id,
            "tier_granted": target_tier if user else None,
        }

    async def _find_user(self, message: str, from_name: str, email: str) -> User | None:
        """
        Estrategia de resolución multicapa para identificar al usuario de Telegram:
        1. Buscar ID numérico de Telegram en el campo message (ej. 'id: 133994080' o '133994080').
        2. Buscar @username en el campo message.
        3. Buscar @username en el campo from_name.
        4. Buscar por dirección de email en la base de datos de usuarios.
        """
        # Paso 1: Regex para Telegram ID en el mensaje
        if message:
            # Coincidencias tipo 'id: 12345678', 'tg: 12345678', '#12345678' o un número de 6-12 dígitos
            id_match = re.search(
                r"(?:id|tg|telegram)?\s*[:#=]?\s*(\d{6,12})\b", message, re.IGNORECASE
            )
            if id_match:
                try:
                    candidate_id = int(id_match.group(1))
                    user = await user_repo.get_by_id(candidate_id)
                    if user:
                        logger.info(
                            f"🔍 Usuario encontrado por ID en mensaje de Ko-fi: {candidate_id}"
                        )
                        return user
                except Exception as e:  # noqa: BLE001
                    logger.debug(f"Error comprobando candidato por ID: {e}")

            # Paso 2: Regex para @username en el mensaje
            user_match = re.search(r"@([a-zA-Z0-9_]{4,32})\b", message)
            if user_match:
                cand_username = user_match.group(1).lower()
                user = await self._find_user_by_username(cand_username)
                if user:
                    logger.info(
                        f"🔍 Usuario encontrado por @username en mensaje de Ko-fi: @{cand_username}"
                    )
                    return user

        # Paso 3: @username en from_name
        if from_name:
            fn = from_name.strip()
            if fn.startswith("@"):
                cand_username = fn[1:].lower()
                user = await self._find_user_by_username(cand_username)
                if user:
                    logger.info(
                        f"🔍 Usuario encontrado por from_name @username en Ko-fi: @{cand_username}"
                    )
                    return user

        # Paso 4: Búsqueda por Email
        if email:
            try:
                user = await user_repo.get_by_email(email)
                if user:
                    logger.info(f"🔍 Usuario encontrado por email en Ko-fi: {email}")
                    return user
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Error buscando usuario por email: {e}")

        return None

    async def _find_user_by_username(self, username: str) -> User | None:
        """Busca un usuario en Postgres por su username de Telegram (case-insensitive)."""
        if not username:
            return None
        try:
            async with pg_manager.get_session() as session:
                stmt = select(User).where(func.lower(User.username) == username.lower())
                res = await session.execute(stmt)
                return res.scalar_one_or_none()
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error buscando por username {username}: {e}")
            return None

    async def _determine_tier_and_duration(
        self, amount: float, tier_name: str | None, is_subscription: bool
    ) -> tuple[str, int]:
        """
        Determina el nivel asignado y la duración en días basándose en:
        - El nombre del tier (si Ko-fi lo especifica en la suscripción).
        - El monto donado en comparación con las configuraciones (price_whitelist, price_vip, price_premium).
        """
        p_white = float(get_setting("price_whitelist", "5"))
        p_vip = float(get_setting("price_vip", "10"))
        p_premium = float(get_setting("price_premium", "20"))
        default_months = int(get_setting("benefit_duration_months", "6"))

        # 1. Determinar nivel
        target_tier = "patrocinador"
        if tier_name:
            t_lower = tier_name.lower()
            if any(k in t_lower for k in ["premium", "gold", "oro"]):
                target_tier = "premium"
            elif any(k in t_lower for k in ["vip", "silver", "plata"]):
                target_tier = "vip"
            elif any(
                k in t_lower for k in ["patrocinador", "whitelist", "bronze", "bronce"]
            ):
                target_tier = "patrocinador"
            else:
                target_tier = "patrocinador"
        else:
            if amount >= p_premium:
                target_tier = "premium"
            elif amount >= p_vip:
                target_tier = "vip"
            elif amount >= p_white:
                target_tier = "patrocinador"
            else:
                target_tier = "patrocinador"

        # 2. Determinar duración
        if is_subscription:
            # Suscripción mensual recurrente: se renueva 30 días con cada cobro
            duration_days = 30
        else:
            # Donación única: duración según meses configurados
            duration_days = max(30, default_months * 30)

        return target_tier, duration_days

    async def _notify_user(
        self,
        telegram_id: int,
        display_name: str,
        amount: float,
        currency: str,
        target_tier: str,
        duration_days: int,
        is_subscription: bool,
    ):
        """Envía notificación directa por Telegram al donador."""
        try:
            from api.main import bot

            if (
                not bot
                or not getattr(bot, "app", None)
                or not getattr(bot.app, "bot", None)
            ):
                logger.warning(
                    "Bot de Telegram no inicializado; no se pudo enviar confirmación al usuario."
                )
                return

            sub_text = "suscripción mensual" if is_subscription else "donación"
            msg = (
                f"☕ <b>¡Muchas gracias por tu apoyo en Ko-fi!</b>\n\n"
                f"Hola <b>{display_name}</b>, hemos recibido y validado tu {sub_text} de <b>{amount:.2f} {currency}</b>.\n\n"
                f"✨ Tu cuenta ha sido activada al nivel <b>⭐ {target_tier.upper()}</b> por <b>{duration_days} días</b>.\n"
                f"Ya puedes disfrutar de tus descargas y beneficios exclusivos en ZeePub.\n\n"
                f"<i>¡Gracias por ayudar a mantener activo este proyecto!</i>"
            )
            await bot.app.bot.send_message(
                chat_id=telegram_id,
                text=msg,
                parse_mode="HTML",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"No se pudo enviar mensaje de confirmación al usuario {telegram_id}: {e}"
            )

    async def _notify_admins(
        self,
        from_name: str,
        amount: float,
        currency: str,
        payment_type: str,
        tier_name: str | None,
        target_tier: str,
        duration_days: int,
        email: str,
        message: str,
        tx_id: str,
        user: User | None,
    ):
        """Envía alerta de donación a los administradores configurados."""
        try:
            from api.main import bot

            if (
                not bot
                or not getattr(bot, "app", None)
                or not getattr(bot.app, "bot", None)
            ):
                return

            alert_users = config.STATUS_ALERT_USERS or {config.SUPER_ADMIN_ID}

            if user:
                text = (
                    f"☕ <b>Nueva donación recibida en Ko-fi</b>\n\n"
                    f"• <b>Usuario:</b> {user.name or user.nickname or user.username} (<code>{user.telegram_id}</code>)\n"
                    f"• <b>Monto:</b> {amount:.2f} {currency} ({payment_type})\n"
                    f"• <b>Nivel asignado:</b> ⭐ {target_tier.upper()} ({duration_days} días)\n"
                    f"• <b>Email:</b> {email or 'N/A'}\n"
                    f"• <b>Mensaje:</b> <i>{message or 'Sin mensaje'}</i>\n"
                    f"• <b>Tx ID:</b> <code>{tx_id}</code>"
                )
            else:
                text = (
                    f"⚠️ <b>Donación en Ko-fi sin vincular automáticamente</b>\n\n"
                    f"• <b>De:</b> {from_name or 'Anónimo'}\n"
                    f"• <b>Email:</b> {email or 'N/A'}\n"
                    f"• <b>Monto:</b> {amount:.2f} {currency} ({payment_type})\n"
                    f"• <b>Tier Ko-fi:</b> {tier_name or 'N/A'}\n"
                    f"• <b>Mensaje del donador:</b> <i>{message or 'Sin mensaje'}</i>\n"
                    f"• <b>Tx ID:</b> <code>{tx_id}</code>\n\n"
                    f"<i>ℹ️ El usuario no indicó su ID de Telegram ni coincidió por correo. "
                    f"Usa <code>/link_donacion {tx_id} &lt;telegram_id&gt;</code> para vincularla manualmente.</i>"
                )

            for admin_id in alert_users:
                try:
                    await bot.app.bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        parse_mode="HTML",
                    )
                except Exception as ex:  # noqa: BLE001
                    logger.debug(f"Error alertando al admin {admin_id}: {ex}")

        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Error enviando notificación administrativa de donación: {e}"
            )


kofi_service = KofiService()
