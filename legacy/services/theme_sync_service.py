import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.theme_sync_models import ThemeSyncLog
from models.users import AppTheme

logger = logging.getLogger(__name__)


class ThemeSyncService:
    """Servicio de sincronización de temas entre PostgreSQL local y Supabase."""

    def __init__(self):
        self.last_sync_key = "last_theme_sync"

    async def get_local_themes(self, session: AsyncSession) -> list[dict[str, Any]]:
        """Obtener todos los temas de la base de datos local."""
        stmt = select(AppTheme).order_by(AppTheme.name)
        result = await session.execute(stmt)
        themes = result.scalars().all()

        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "theme_type": t.theme_type,
                "primary_color": t.primary_color,
                "background_color": t.background_color,
                "card_color": t.card_color,
                "glass_opacity": t.glass_opacity,
                "nav_opacity": t.nav_opacity,
                "accent_opacity": t.accent_opacity,
                "glass_blur": t.glass_blur,
                "card_glow_intensity": t.card_glow_intensity,
                "font_size": t.font_size,
                "cover_width": t.cover_width,
                "banner_content_offset": t.banner_content_offset,
                "updated_at": t.updated_at,
            }
            for t in themes
        ]

    async def ensure_theme_sync_logs_table(self, session: AsyncSession):
        """Asegurar que la tabla theme_sync_logs exista."""
        try:
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS theme_sync_logs (
                    id SERIAL PRIMARY KEY,
                    sync_type VARCHAR(50) NOT NULL,
                    direction VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    local_themes_before INTEGER DEFAULT 0,
                    local_themes_after INTEGER DEFAULT 0,
                    supabase_themes_before INTEGER DEFAULT 0,
                    supabase_themes_after INTEGER DEFAULT 0,
                    themes_added INTEGER DEFAULT 0,
                    themes_updated INTEGER DEFAULT 0,
                    themes_deleted INTEGER DEFAULT 0,
                    errors TEXT,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            )

            # Crear índices
            await session.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_theme_sync_logs_status ON theme_sync_logs(status)
            """)
            )

            await session.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_theme_sync_logs_started_at ON theme_sync_logs(started_at)
            """)
            )

            await session.commit()
            logger.info("theme_sync_logs table ensured")
        except Exception as e:
            logger.error(f"Error ensuring theme_sync_logs table: {e}")
            raise

    async def get_supabase_themes(self) -> list[dict[str, Any]]:
        """Obtener todos los temas de Supabase."""
        if not supabase_manager.is_active:
            return []

        try:
            result = supabase_manager.get_client().table("app_themes").select("*").execute()
            return result.data if result and result.data else []
        except Exception as e:
            logger.error(f"Error getting Supabase themes: {e}")
            return []

    def theme_to_dict(self, theme: AppTheme) -> dict[str, Any]:
        """Convertir AppTheme a diccionario."""
        return {
            "id": theme.id,
            "name": theme.name,
            "description": theme.description,
            "theme_type": theme.theme_type,
            "primary_color": theme.primary_color,
            "background_color": theme.background_color,
            "card_color": theme.card_color,
            "glass_opacity": theme.glass_opacity,
            "nav_opacity": theme.nav_opacity,
            "accent_opacity": theme.accent_opacity,
            "glass_blur": theme.glass_blur,
            "card_glow_intensity": theme.card_glow_intensity,
            "font_size": theme.font_size,
            "cover_width": theme.cover_width,
            "banner_content_offset": theme.banner_content_offset,
            "updated_at": theme.updated_at.isoformat() if theme.updated_at else None,
        }

    def normalize_theme_data(self, theme_data: dict[str, Any]) -> dict[str, Any]:
        """Normalizar datos de tema para compatibilidad."""
        # Trim name to avoid duplicates with trailing spaces
        name = theme_data.get("name", "").strip() if theme_data.get("name") else ""

        normalized = {
            "name": name,
            "description": theme_data.get("description"),
            "theme_type": theme_data.get("theme_type") or theme_data.get("theme") or "dark",
            "primary_color": theme_data.get("primary_color") or theme_data.get("primaryColor"),
            "background_color": theme_data.get("background_color") or theme_data.get("backgroundColor"),
            "card_color": theme_data.get("card_color") or theme_data.get("cardColor"),
            "glass_opacity": theme_data.get("glass_opacity") or theme_data.get("glassOpacity"),
            "nav_opacity": theme_data.get("nav_opacity") or theme_data.get("navOpacity"),
            "accent_opacity": theme_data.get("accent_opacity") or theme_data.get("accentOpacity"),
            "glass_blur": theme_data.get("glass_blur") or theme_data.get("glassBlur"),
            "card_glow_intensity": theme_data.get("card_glow_intensity") or theme_data.get("cardGlowIntensity"),
            "font_size": theme_data.get("font_size") or theme_data.get("fontSize"),
            "cover_width": theme_data.get("cover_width") or theme_data.get("coverWidth"),
            "banner_content_offset": theme_data.get("banner_content_offset") or theme_data.get("bannerContentOffset"),
        }

        # Handle updated_at safely for local DB
        updated_at = theme_data.get("updated_at")
        if updated_at:
            if isinstance(updated_at, str):
                try:
                    from dateutil import parser

                    updated_at = parser.isoparse(updated_at)
                except Exception:
                    updated_at = datetime.utcnow()
            elif not isinstance(updated_at, datetime):
                updated_at = datetime.utcnow()
        else:
            updated_at = datetime.utcnow()

        # Ensure naive datetime for local PostgreSQL (naive columns)
        if updated_at and updated_at.tzinfo:
            updated_at = updated_at.replace(tzinfo=None)

        normalized["updated_at"] = updated_at
        return normalized

    async def fix_theme_sequence(self, session: AsyncSession):
        """Asegura que la secuencia del ID de app_themes esté sincronizada con los datos."""
        try:
            # PostgreSQL specific: Reset sequence to max(id)
            # Usamos COALESCE para manejar el caso de tabla vacía
            await session.execute(
                text("SELECT setval('app_themes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM app_themes))")
            )
            await session.commit()
            logger.info("app_themes_id_seq synchronized with max(id)")
        except Exception as e:
            logger.error(f"Error fixing theme sequence: {e}")
            await session.rollback()

    async def sync_supabase_to_local(self, session: AsyncSession) -> tuple[int, int]:
        """Sincronizar temas de Supabase a la base de datos local de forma robusta."""
        # 0. Asegurar secuencia
        await self.fix_theme_sequence(session)

        supabase_themes = await self.get_supabase_themes()

        # Obtener todos los temas locales para mapeo y limpieza
        local_result = await session.execute(select(AppTheme))
        local_themes_objs = local_result.scalars().all()

        local_map = {}
        duplicates = []

        for t in local_themes_objs:
            norm_name = t.name.strip().lower()
            if norm_name in local_map:
                duplicates.append(t)
            else:
                local_map[norm_name] = t

        # 1. Limpiar duplicados locales si existen
        if duplicates:
            logger.warning(f"Se encontraron {len(duplicates)} temas duplicados localmente. Eliminando...")
            for dup in duplicates:
                await session.delete(dup)
            await session.flush()

        added_count = 0
        updated_count = 0

        # 2. Procesar temas de Supabase
        for supabase_theme in supabase_themes:
            if not supabase_theme.get("name"):
                continue

            theme_data = self.normalize_theme_data(supabase_theme)
            norm_name = supabase_theme["name"].strip().lower()

            if norm_name not in local_map:
                # Agregar nuevo tema
                new_theme = AppTheme(**theme_data)
                session.add(new_theme)
                local_map[norm_name] = new_theme  # Evitar duplicados en el mismo loop
                added_count += 1
                logger.debug(f"Sincronización: Agregado tema '{supabase_theme['name']}'")
            else:
                # Actualizar tema existente
                existing_theme = local_map[norm_name]
                for key, value in theme_data.items():
                    if value is not None:
                        setattr(existing_theme, key, value)
                updated_count += 1
                logger.debug(f"Sincronización: Actualizado tema '{supabase_theme['name']}'")

        await session.commit()
        return added_count, updated_count

    async def sync_local_to_supabase(self, session: AsyncSession) -> tuple[int, int]:
        """Sincronizar temas de la base de datos local a Supabase."""
        if not supabase_manager.is_active:
            return 0, 0

        local_themes = await self.get_local_themes(session)
        supabase_themes = await self.get_supabase_themes()

        supabase_names = {t["name"] for t in supabase_themes}
        added_count = 0
        updated_count = 0

        for local_theme in local_themes:
            # Create payload for Supabase - exclude internal/managed columns
            theme_payload = self.normalize_theme_data(local_theme)
            if "updated_at" in theme_payload:
                del theme_payload["updated_at"]
            if "id" in theme_payload:
                del theme_payload["id"]

            if local_theme["name"] not in supabase_names:
                # Agregar a Supabase
                try:
                    result = supabase_manager.get_client().table("app_themes").insert(theme_payload).execute()
                    if result:
                        added_count += 1
                        logger.info(f"Added theme to Supabase: {local_theme['name']}")
                except Exception as e:
                    logger.error(f"Error adding theme to Supabase: {e}")
            else:
                # Actualizar en Supabase
                try:
                    result = (
                        supabase_manager.get_client()
                        .table("app_themes")
                        .update(theme_payload)
                        .eq("name", local_theme["name"])
                        .execute()
                    )
                    if result:
                        updated_count += 1
                        logger.info(f"Updated theme in Supabase: {local_theme['name']}")
                except Exception as e:
                    logger.error(f"Error updating theme in Supabase: {e}")

        return added_count, updated_count

    async def log_sync(self, session: AsyncSession, sync_log: ThemeSyncLog):
        """Guardar registro de sincronización."""
        session.add(sync_log)
        await session.commit()

    async def initial_sync(self) -> dict[str, Any]:
        """Sincronización inicial al iniciar el bot."""
        if not supabase_manager.is_active:
            logger.warning("Supabase not active, skipping initial sync")
            return {"status": "skipped", "reason": "Supabase not active"}

        logger.info("Starting initial theme sync from Supabase to local")

        async with pg_manager.get_session() as session:
            # Asegurar que la tabla de logs exista
            await self.ensure_theme_sync_logs_table(session)

            # Contar temas antes
            local_before = len(await self.get_local_themes(session))
            supabase_before = len(await self.get_supabase_themes())

            # Crear log de sincronización
            sync_log = ThemeSyncLog(
                sync_type="initial",
                direction="supabase_to_local",
                status="running",
                local_themes_before=local_before,
                supabase_themes_before=supabase_before,
                started_at=datetime.utcnow(),
            )

            try:
                # Sincronizar de Supabase a local
                added, updated = await self.sync_supabase_to_local(session)

                # Contar temas después
                local_after = len(await self.get_local_themes(session))

                # Actualizar log
                sync_log.status = "success"
                sync_log.local_themes_after = local_after
                sync_log.themes_added = added
                sync_log.themes_updated = updated
                sync_log.completed_at = datetime.utcnow()

                await self.log_sync(session, sync_log)

                logger.info(f"Initial sync completed: {added} added, {updated} updated")

                return {
                    "status": "success",
                    "added": added,
                    "updated": updated,
                    "local_before": local_before,
                    "local_after": local_after,
                }

            except Exception as e:
                sync_log.status = "error"
                sync_log.errors = str(e)
                sync_log.completed_at = datetime.utcnow()
                await self.log_sync(session, sync_log)

                logger.error(f"Initial sync failed: {e}")
                return {"status": "error", "error": str(e)}

    async def daily_sync(self) -> dict[str, Any]:
        """Sincronización diaria bidireccional."""
        logger.info("Starting daily bidirectional theme sync")

        async with pg_manager.get_session() as session:
            # Asegurar que la tabla de logs exista
            await self.ensure_theme_sync_logs_table(session)

            local_before = len(await self.get_local_themes(session))
            supabase_before = len(await self.get_supabase_themes())

            sync_log = ThemeSyncLog(
                sync_type="daily",
                direction="bidirectional",
                status="running",
                local_themes_before=local_before,
                supabase_themes_before=supabase_before,
                started_at=datetime.utcnow(),
            )

            try:
                # Sincronizar en ambas direcciones
                local_added, local_updated = await self.sync_supabase_to_local(session)
                supabase_added, supabase_updated = await self.sync_local_to_supabase(session)

                local_after = len(await self.get_local_themes(session))
                supabase_after = len(await self.get_supabase_themes())

                sync_log.status = "success"
                sync_log.local_themes_after = local_after
                sync_log.supabase_themes_after = supabase_after
                sync_log.themes_added = local_added + supabase_added
                sync_log.themes_updated = local_updated + supabase_updated
                sync_log.completed_at = datetime.utcnow()

                await self.log_sync(session, sync_log)

                logger.info(
                    f"Daily sync completed: Local: {local_added} added, {local_updated} updated; Supabase: {supabase_added} added, {supabase_updated} updated"
                )

                return {
                    "status": "success",
                    "local_added": local_added,
                    "local_updated": local_updated,
                    "supabase_added": supabase_added,
                    "supabase_updated": supabase_updated,
                }

            except Exception as e:
                sync_log.status = "error"
                sync_log.errors = str(e)
                sync_log.completed_at = datetime.utcnow()
                await self.log_sync(session, sync_log)

                logger.error(f"Daily sync failed: {e}")
                return {"status": "error", "error": str(e)}

    async def manual_sync(self) -> dict[str, Any]:
        """Sincronización manual iniciada por el admin."""
        logger.info("Starting manual bidirectional theme sync")

        async with pg_manager.get_session() as session:
            # Asegurar que la tabla de logs exista
            await self.ensure_theme_sync_logs_table(session)

            local_before = len(await self.get_local_themes(session))
            supabase_before = len(await self.get_supabase_themes())

            sync_log = ThemeSyncLog(
                sync_type="manual",
                direction="bidirectional",
                status="running",
                local_themes_before=local_before,
                supabase_themes_before=supabase_before,
                started_at=datetime.utcnow(),
            )

            try:
                # Sincronizar en ambas direcciones
                local_added, local_updated = await self.sync_supabase_to_local(session)
                supabase_added, supabase_updated = await self.sync_local_to_supabase(session)

                local_after = len(await self.get_local_themes(session))
                supabase_after = len(await self.get_supabase_themes())

                sync_log.status = "success"
                sync_log.local_themes_after = local_after
                sync_log.supabase_themes_after = supabase_after
                sync_log.themes_added = local_added + supabase_added
                sync_log.themes_updated = local_updated + supabase_updated
                sync_log.completed_at = datetime.utcnow()

                await self.log_sync(session, sync_log)

                logger.info(
                    f"Manual sync completed: Local: {local_added} added, {local_updated} updated; Supabase: {supabase_added} added, {supabase_updated} updated"
                )

                # Invalidate Caches
                from services.theme_service import theme_service

                await theme_service.invalidate_caches()

                return {
                    "status": "success",
                    "local_added": local_added,
                    "local_updated": local_updated,
                    "supabase_added": supabase_added,
                    "supabase_updated": supabase_updated,
                }

            except Exception as e:
                sync_log.status = "error"
                sync_log.errors = str(e)
                sync_log.completed_at = datetime.utcnow()
                await self.log_sync(session, sync_log)

                logger.error(f"Manual sync failed: {e}")
                return {"status": "error", "error": str(e)}

    async def get_sync_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        """Obtener historial de sincronizaciones."""
        async with pg_manager.get_session() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM theme_sync_logs
                    ORDER BY started_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            rows = result.fetchall()

            logs = []
            for row in rows:
                log_dict = dict(row)
                if log_dict.get("started_at"):
                    log_dict["started_at"] = log_dict["started_at"].isoformat()
                if log_dict.get("completed_at"):
                    log_dict["completed_at"] = log_dict["completed_at"].isoformat()
                logs.append(log_dict)

            return logs


# Instancia global
theme_sync_service = ThemeSyncService()
