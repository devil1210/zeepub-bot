import logging
from typing import Any

from sqlalchemy import func, select

from core.db_manager_pg import pg_manager
from models.library import GroupContactLink, TranslatorsGroup

logger = logging.getLogger(__name__)


class WorkgroupService:
    """
    Servicio para la gestión de Grupos Traductores y sus enlaces oficiales de contacto
    (alineado con el ERD WORKGROUP y GROUP_CONTACT_LINK de zeepubs_server).
    """

    @staticmethod
    async def get_by_id(group_id: int) -> TranslatorsGroup | None:
        """Obtiene un grupo traductor por su ID."""
        try:
            async with pg_manager.get_session() as session:
                stmt = select(TranslatorsGroup).where(TranslatorsGroup.id == group_id)
                res = await session.execute(stmt)
                return res.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error obteniendo grupo traductor {group_id}: {e}")
            return None

    @staticmethod
    async def get_by_name(name: str) -> TranslatorsGroup | None:
        """Busca un grupo traductor por nombre (case-insensitive)."""
        if not name or not name.strip():
            return None
        try:
            async with pg_manager.get_session() as session:
                clean_name = name.strip()
                stmt = select(TranslatorsGroup).where(
                    func.lower(TranslatorsGroup.name) == clean_name.lower()
                )
                res = await session.execute(stmt)
                return res.scalar_one_or_none()
        except Exception as e:
            logger.debug(f"Error buscando grupo traductor por nombre '{name}': {e}")
            return None

    @staticmethod
    async def get_or_create_group(
        name: str,
        siglas: str | None = None,
        description: str | None = None,
    ) -> TranslatorsGroup | None:
        """Obtiene o crea un grupo traductor asegurando consistencia."""
        if not name or not name.strip():
            return None

        clean_name = name.strip()
        try:
            async with pg_manager.get_session() as session:
                stmt = select(TranslatorsGroup).where(
                    func.lower(TranslatorsGroup.name) == clean_name.lower()
                )
                res = await session.execute(stmt)
                group = res.scalar_one_or_none()

                if not group:
                    group = TranslatorsGroup(
                        name=clean_name,
                        siglas=siglas.strip() if siglas else None,
                        description=description.strip() if description else None,
                    )
                    session.add(group)
                    await session.flush()
                    await session.refresh(group)
                    logger.info(f"✅ Grupo traductor registrado: '{clean_name}' (ID: {group.id})")

                return group
        except Exception as e:
            logger.error(f"Error en get_or_create_group para '{name}': {e}")
            return None

    @staticmethod
    async def set_contact_link(
        group_id: int,
        platform: str,
        url: str,
    ) -> bool:
        """Añade o actualiza un enlace de contacto oficial para un grupo."""
        if not group_id or not platform or not url:
            return False

        clean_platform = platform.strip().lower()
        clean_url = url.strip()

        try:
            async with pg_manager.get_session() as session:
                stmt = select(GroupContactLink).where(
                    GroupContactLink.group_id == group_id,
                    func.lower(GroupContactLink.platform) == clean_platform,
                )
                res = await session.execute(stmt)
                link = res.scalar_one_or_none()

                if link:
                    link.url = clean_url
                else:
                    link = GroupContactLink(
                        group_id=group_id,
                        platform=clean_platform,
                        url=clean_url,
                    )
                    session.add(link)

                await session.commit()
                logger.info(f"✅ Enlace [{clean_platform}] guardado para grupo {group_id}: {clean_url}")
                return True
        except Exception as e:
            logger.error(f"Error guardando enlace de contacto: {e}")
            return False

    @staticmethod
    async def resolve_translator_metadata(
        translator_name: str | None = None,
        group_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Resuelve metadatos y enlaces de traducción listos para usar en plantillas:
        - traductor / grupo: Nombre del grupo/traductor
        - traductor_link / grupo_link: Mejor enlace según prioridad (Web > FB > Discord > Patreon)
        - traductor_web: Enlace Web oficial
        - traductor_fb: Enlace Facebook
        - traductor_discord: Enlace Discord
        - traductor_patreon: Enlace Patreon
        - traductor_twitter: Enlace Twitter/X
        - traductor_links: Texto consolidado con los enlaces disponibles
        """
        res_data: dict[str, Any] = {
            "traductor": translator_name or "",
            "grupo": translator_name or "",
            "traductor_link": "",
            "grupo_link": "",
            "traductor_web": "",
            "traductor_fb": "",
            "traductor_discord": "",
            "traductor_patreon": "",
            "traductor_twitter": "",
            "traductor_links": "",
        }

        group = None
        if group_id:
            group = await WorkgroupService.get_by_id(group_id)
        elif translator_name:
            group = await WorkgroupService.get_by_name(translator_name)

        if group:
            res_data["traductor"] = group.name
            res_data["grupo"] = group.name
            preferred = group.get_preferred_link()
            if preferred:
                res_data["traductor_link"] = preferred
                res_data["grupo_link"] = preferred

            links_dict = group.get_links_dict()
            res_data["traductor_web"] = links_dict.get("web", "")
            res_data["traductor_fb"] = links_dict.get("fb", "")
            res_data["traductor_discord"] = links_dict.get("discord", "")
            res_data["traductor_patreon"] = links_dict.get("patreon", "")
            res_data["traductor_twitter"] = links_dict.get("twitter", "")

            # Construir texto consolidado de enlaces
            formatted_links = []
            if res_data["traductor_web"]:
                formatted_links.append(f"🌐 Web: {res_data['traductor_web']}")
            if res_data["traductor_fb"]:
                formatted_links.append(f"📘 Facebook: {res_data['traductor_fb']}")
            if res_data["traductor_discord"]:
                formatted_links.append(f"💬 Discord: {res_data['traductor_discord']}")
            if res_data["traductor_patreon"]:
                formatted_links.append(f"🧡 Patreon: {res_data['traductor_patreon']}")
            if res_data["traductor_twitter"]:
                formatted_links.append(f"🐦 Twitter: {res_data['traductor_twitter']}")

            res_data["traductor_links"] = " | ".join(formatted_links)

        return res_data


workgroup_service = WorkgroupService()
