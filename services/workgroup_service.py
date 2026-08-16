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

    @staticmethod
    async def assign_workgroup_to_book(
        book_id: str,
        workgroup_id: int,
        role: str = "translator",
    ) -> bool:
        """
        Asocia un grupo de traducción, edición o maquetación directamente a un Libro por su UUID / ID.
        """
        if not book_id or not workgroup_id:
            return False

        clean_role = role.strip().lower()

        try:
            from models.library import Book, BookWorkgroup

            async with pg_manager.get_session() as session:
                # 1. Actualizar columna directa en Book si coincide con roles principales
                book_stmt = select(Book).where(Book.id == book_id)
                book_res = await session.execute(book_stmt)
                book = book_res.scalar_one_or_none()

                if book:
                    if clean_role in ("translator", "traductor"):
                        book.translator_group_id = workgroup_id
                    elif clean_role in ("editor", "corrector", "proofreader"):
                        book.editor_group_id = workgroup_id
                    elif clean_role in ("layout", "maquetador", "typesetter"):
                        book.layout_group_id = workgroup_id

                # 2. Registrar en tabla asociativa BookWorkgroup
                bw_stmt = select(BookWorkgroup).where(
                    BookWorkgroup.book_id == book_id,
                    BookWorkgroup.workgroup_id == workgroup_id,
                    BookWorkgroup.role == clean_role,
                )
                bw_res = await session.execute(bw_stmt)
                bw = bw_res.scalar_one_or_none()

                if not bw:
                    new_bw = BookWorkgroup(
                        book_id=book_id,
                        workgroup_id=workgroup_id,
                        role=clean_role,
                    )
                    session.add(new_bw)

                await session.commit()
                logger.info(
                    f"✅ Grupo {workgroup_id} asignado a Libro {book_id} con rol '{clean_role}'"
                )
                return True
        except Exception as e:
            logger.error(f"Error asignando grupo a libro {book_id}: {e}")
            return False

    @staticmethod
    async def resolve_book_workgroup_credits(
        book_id: str | None = None,
        book_obj: Any | None = None,
        raw_meta: dict[str, Any] | None = None,
        public_link: str | None = None,
    ) -> dict[str, Any]:
        """
        Resuelve todos los créditos y enlaces por UUID de libro para plantillas:
        - Traductor: {traductor}, {traductor_link}, {traductor_web}, {traductor_fb}, {traductor_discord}, {traductor_links}
        - Editor: {editor}, {editor_link}, {editor_web}, {editor_fb}, {editor_discord}, {editor_links}
        - Maquetador: {maquetador}, {maquetador_link}, {maquetador_web}, {maquetador_fb}, {maquetador_discord}, {maquetador_links}
        """
        raw_meta = raw_meta or {}
        res: dict[str, Any] = {}

        # 1. Resolver Traductor Individual y Grupo Traductor
        t_individual = raw_meta.get("traductor") or raw_meta.get("translator") or (getattr(book_obj, "translator", None) if book_obj else None) or ""
        g_name = raw_meta.get("grupo_traductor") or raw_meta.get("grupo")
        t_gid = getattr(book_obj, "translator_group_id", None) if book_obj else None

        t_group = await WorkgroupService.get_by_id(t_gid) if t_gid else (await WorkgroupService.get_by_name(g_name) if g_name else (await WorkgroupService.get_by_name(t_individual) if t_individual else None))

        group_name = t_group.name if t_group else (g_name or t_individual)
        preferred_group_link = t_group.get_preferred_link() if t_group else ""
        g_links = t_group.get_links_dict() if t_group else {}

        # Tags de Grupo Traductor
        res["grupo"] = group_name
        res["grupo_traductor"] = group_name
        res["grupo_link"] = preferred_group_link
        res["grupo_web"] = g_links.get("web", "")
        res["grupo_fb"] = g_links.get("fb", "")
        res["grupo_discord"] = g_links.get("discord", "")
        res["grupo_patreon"] = g_links.get("patreon", "")
        res["grupo_twitter"] = g_links.get("twitter", "")

        formatted_g = []
        if res["grupo_web"]:
            formatted_g.append(f"🌐 Web: {res['grupo_web']}")
        if res["grupo_fb"]:
            formatted_g.append(f"📘 Facebook: {res['grupo_fb']}")
        if res["grupo_discord"]:
            formatted_g.append(f"💬 Discord: {res['grupo_discord']}")
        if res["grupo_patreon"]:
            formatted_g.append(f"🧡 Patreon: {res['grupo_patreon']}")
        if res["grupo_twitter"]:
            formatted_g.append(f"🐦 Twitter: {res['grupo_twitter']}")
        res["grupo_links"] = " | ".join(formatted_g)

        # Tags de Traductor (Persona / Individual)
        res["traductor"] = t_individual or group_name
        res["translator"] = res["traductor"]
        res["traductor_link"] = preferred_group_link
        res["traductor_web"] = res["grupo_web"]
        res["traductor_fb"] = res["grupo_fb"]
        res["traductor_discord"] = res["grupo_discord"]
        res["traductor_patreon"] = res["grupo_patreon"]
        res["traductor_twitter"] = res["grupo_twitter"]
        res["traductor_links"] = res["grupo_links"]

        # 2. Resolver Editor
        e_name = raw_meta.get("editor") or (getattr(book_obj, "editor", None) if book_obj else None)
        e_gid = getattr(book_obj, "editor_group_id", None) if book_obj else None
        e_group = await WorkgroupService.get_by_id(e_gid) if e_gid else (await WorkgroupService.get_by_name(e_name) if e_name else None)

        res["editor"] = e_group.name if e_group else (e_name or "")
        res["editor_link"] = e_group.get_preferred_link() if e_group else ""
        e_links = e_group.get_links_dict() if e_group else {}
        res["editor_web"] = e_links.get("web", "")
        res["editor_fb"] = e_links.get("fb", "")
        res["editor_discord"] = e_links.get("discord", "")
        res["editor_patreon"] = e_links.get("patreon", "")
        res["editor_twitter"] = e_links.get("twitter", "")
        formatted_e = []
        if res["editor_web"]:
            formatted_e.append(f"🌐 Web: {res['editor_web']}")
        if res["editor_fb"]:
            formatted_e.append(f"📘 Facebook: {res['editor_fb']}")
        if res["editor_discord"]:
            formatted_e.append(f"💬 Discord: {res['editor_discord']}")
        res["editor_links"] = " | ".join(formatted_e)

        # 3. Resolver Maquetador
        m_name = raw_meta.get("maquetador") or raw_meta.get("layout_by") or (getattr(book_obj, "layout_by", None) if book_obj else None)
        m_gid = getattr(book_obj, "layout_group_id", None) if book_obj else None
        m_group = await WorkgroupService.get_by_id(m_gid) if m_gid else (await WorkgroupService.get_by_name(m_name) if m_name else None)

        res["maquetador"] = m_group.name if m_group else (m_name or "")
        res["layout_by"] = res["maquetador"]
        res["maquetador_link"] = m_group.get_preferred_link() if m_group else ""
        m_links = m_group.get_links_dict() if m_group else {}
        res["maquetador_web"] = m_links.get("web", "")
        res["maquetador_fb"] = m_links.get("fb", "")
        res["maquetador_discord"] = m_links.get("discord", "")
        res["maquetador_patreon"] = m_links.get("patreon", "")
        res["maquetador_twitter"] = m_links.get("twitter", "")
        formatted_m = []
        if res["maquetador_web"]:
            formatted_m.append(f"🌐 Web: {res['maquetador_web']}")
        if res["maquetador_fb"]:
            formatted_m.append(f"📘 Facebook: {res['maquetador_fb']}")
        if res["maquetador_discord"]:
            formatted_m.append(f"💬 Discord: {res['maquetador_discord']}")
        res["maquetador_links"] = " | ".join(formatted_m)

        return res


workgroup_service = WorkgroupService()
