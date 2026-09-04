import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.orm import selectinload

from api.handlers.helpers import check_admin, check_staff
from core.db_manager_pg import pg_manager
from models.library import BookWorkgroup, GroupContactLink, LocalBook, TranslatorsGroup
from services.workgroup_service import WorkgroupService

logger = logging.getLogger(__name__)


async def handle_workgroup_get_all(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna la lista completa de grupos traductores con sus enlaces y estadísticas."""
    check_staff(user_data)

    try:
        async with pg_manager.get_session() as session:
            stmt = (
                select(TranslatorsGroup)
                .options(selectinload(TranslatorsGroup.contact_links))
                .order_by(TranslatorsGroup.name.asc())
            )

            res = await session.execute(stmt)
            groups = res.scalars().all()

            # Obtener conteo exhaustivo de libros asociados a cada grupo (vía translator, editor, layout o BookWorkgroup)
            count_stmt = text("""
                WITH linked AS (
                    SELECT translator_group_id AS group_id, id AS book_id FROM books WHERE translator_group_id IS NOT NULL
                    UNION ALL
                    SELECT editor_group_id AS group_id, id AS book_id FROM books WHERE editor_group_id IS NOT NULL
                    UNION ALL
                    SELECT layout_group_id AS group_id, id AS book_id FROM books WHERE layout_group_id IS NOT NULL
                    UNION ALL
                    SELECT workgroup_id AS group_id, book_id FROM book_workgroups
                )
                SELECT group_id, COUNT(DISTINCT book_id)
                FROM linked
                GROUP BY group_id
            """)
            count_res = await session.execute(count_stmt)
            counts_map = {
                row[0]: row[1] for row in count_res.all() if row[0] is not None
            }

            result = []
            for g in groups:
                links_dict = g.get_links_dict()
                result.append(
                    {
                        "id": g.id,
                        "name": g.name,
                        "siglas": g.siglas,
                        "description": g.description,
                        "preferred_link": g.get_preferred_link(),
                        "books_count": counts_map.get(g.id, 0),
                        "links": links_dict,
                        "created_at": g.created_at.isoformat()
                        if g.created_at
                        else None,
                    }
                )

            return {"workgroups": result, "total": len(result)}
    except Exception as e:
        logger.error(f"Error en handle_workgroup_get_all: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_workgroup_save(data: dict[str, Any], user_data: dict[str, Any]):
    """Crea o actualiza un grupo traductor y sus enlaces de contacto."""
    check_admin(user_data)

    group_id = data.get("id")
    name = (data.get("name") or "").strip()
    siglas = (data.get("siglas") or "").strip() or None
    description = (data.get("description") or "").strip() or None
    links = data.get("links") or {}

    if not name:
        raise HTTPException(
            status_code=400, detail="El nombre del grupo es obligatorio"
        )

    try:
        async with pg_manager.get_session() as session:
            if group_id:
                stmt = (
                    select(TranslatorsGroup)
                    .options(selectinload(TranslatorsGroup.contact_links))
                    .where(TranslatorsGroup.id == int(group_id))
                )
                res = await session.execute(stmt)
                group = res.scalar_one_or_none()
                if not group:
                    raise HTTPException(status_code=404, detail="Grupo no encontrado")
                group.name = name
                group.siglas = siglas
                group.description = description
            else:
                group = TranslatorsGroup(
                    name=name, siglas=siglas, description=description
                )
                session.add(group)
                await session.flush()
                await session.refresh(group)

            # Actualizar enlaces de contacto
            valid_platforms = [
                "web",
                "fb",
                "discord",
                "patreon",
                "twitter",
                "donations",
            ]
            for plat in valid_platforms:
                url_val = (links.get(plat) or "").strip()
                link_stmt = select(GroupContactLink).where(
                    GroupContactLink.group_id == group.id,
                    func.lower(GroupContactLink.platform) == plat,
                )
                link_res = await session.execute(link_stmt)
                existing_link = link_res.scalar_one_or_none()

                if url_val:
                    if existing_link:
                        existing_link.url = url_val
                    else:
                        new_link = GroupContactLink(
                            group_id=group.id, platform=plat, url=url_val
                        )
                        session.add(new_link)
                elif existing_link:
                    await session.delete(existing_link)

            await session.commit()
            logger.info(
                f"✅ Grupo traductor guardado exitosamente: {name} (ID: {group.id})"
            )
            return {"success": True, "id": group.id, "name": group.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en handle_workgroup_save: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_workgroup_delete(data: dict[str, Any], user_data: dict[str, Any]):
    """Elimina un grupo traductor desvinculándolo previamente de libros de forma segura."""
    check_admin(user_data)

    group_id = data.get("id")
    if not group_id:
        raise HTTPException(status_code=400, detail="ID de grupo requerido")

    try:
        async with pg_manager.get_session() as session:
            # 1. Desvincular de libros
            await session.execute(
                select(LocalBook).where(LocalBook.translator_group_id == int(group_id))
            )
            # Actualizar a null
            from sqlalchemy import update

            await session.execute(
                update(LocalBook)
                .where(LocalBook.translator_group_id == int(group_id))
                .values(translator_group_id=None)
            )
            await session.execute(
                update(LocalBook)
                .where(LocalBook.editor_group_id == int(group_id))
                .values(editor_group_id=None)
            )
            await session.execute(
                update(LocalBook)
                .where(LocalBook.layout_group_id == int(group_id))
                .values(layout_group_id=None)
            )

            # 2. Eliminar de BookWorkgroup
            await session.execute(
                delete(BookWorkgroup).where(BookWorkgroup.workgroup_id == int(group_id))
            )

            # 3. Eliminar grupo (links se eliminan por cascade)
            del_stmt = delete(TranslatorsGroup).where(
                TranslatorsGroup.id == int(group_id)
            )
            await session.execute(del_stmt)
            await session.commit()

            logger.info(f"🗑️ Grupo traductor {group_id} eliminado exitosamente")
            return {"success": True, "deleted_id": group_id}
    except Exception as e:
        logger.error(f"Error en handle_workgroup_delete: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_workgroup_purge_empty(data: dict[str, Any], user_data: dict[str, Any]):
    """Elimina permanentemente de la base de datos todos los grupos traductores que tengan 0 libros asociados."""
    check_admin(user_data)

    try:
        async with pg_manager.get_session() as session:
            find_empty_stmt = text("""
                WITH linked AS (
                    SELECT translator_group_id AS group_id FROM books WHERE translator_group_id IS NOT NULL
                    UNION ALL
                    SELECT editor_group_id AS group_id FROM books WHERE editor_group_id IS NOT NULL
                    UNION ALL
                    SELECT layout_group_id AS group_id FROM books WHERE layout_group_id IS NOT NULL
                    UNION ALL
                    SELECT workgroup_id AS group_id FROM book_workgroups
                )
                SELECT tg.id FROM translators_groups tg
                WHERE tg.id NOT IN (SELECT DISTINCT group_id FROM linked WHERE group_id IS NOT NULL)
            """)
            res = await session.execute(find_empty_stmt)
            empty_ids = [row[0] for row in res.all()]

            if not empty_ids:
                return {
                    "success": True,
                    "deleted_count": 0,
                    "deleted_ids": [],
                    "message": "No hay grupos traductores con 0 libros para eliminar.",
                }

            # Eliminar enlaces de contacto asociados si existiesen
            await session.execute(
                delete(GroupContactLink).where(GroupContactLink.group_id.in_(empty_ids))
            )
            # Eliminar grupos
            await session.execute(
                delete(TranslatorsGroup).where(TranslatorsGroup.id.in_(empty_ids))
            )
            await session.commit()

            logger.info(
                f"🗑️ Se purgaron {len(empty_ids)} grupos traductores con 0 libros exitosamente"
            )
            return {
                "success": True,
                "deleted_count": len(empty_ids),
                "deleted_ids": empty_ids,
                "message": f"Se eliminaron {len(empty_ids)} grupos traductores con 0 libros exitosamente.",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en handle_workgroup_purge_empty: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def check_epub_metadata_issue(
    epub_publisher: str | None, group_name: str
) -> tuple[bool, str | None]:
    """
    Evalúa si la metadata del publisher dentro del archivo EPUB tiene discrepancias con el nombre canónico del grupo.
    Retorna (has_bad_metadata, issue_description).
    """
    raw_pub = (epub_publisher or "").strip()
    canon_name = (group_name or "").strip()

    if not raw_pub:
        return True, "Etiqueta dc:publisher vacía o ausente dentro del EPUB"

    if raw_pub == canon_name:
        return False, None

    # Casos comunes de discrepancia
    if raw_pub.rstrip(".") == canon_name.rstrip("."):
        if raw_pub.endswith(".") and not canon_name.endswith("."):
            return (
                True,
                f"Punto final sobrante en EPUB: '{raw_pub}' (debe ser '{canon_name}')",
            )
        if canon_name.endswith(".") and not raw_pub.endswith("."):
            return (
                True,
                f"Falta punto final en EPUB: '{raw_pub}' (debe ser '{canon_name}')",
            )

    if raw_pub.lower() == canon_name.lower():
        if raw_pub.isupper() and not canon_name.isupper():
            return (
                True,
                f"Todo en mayúsculas en EPUB: '{raw_pub}' (debe ser '{canon_name}')",
            )
        return (
            True,
            f"Diferencia de mayúsculas/minúsculas: '{raw_pub}' (debe ser '{canon_name}')",
        )

    return True, f"Publisher en archivo difiere: '{raw_pub}' (debe ser '{canon_name}')"


async def handle_workgroup_get_detail(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna los datos completos de un fansub/grupo y todos los libros EPUB vinculados a él con auditoría de metadatos."""
    check_staff(user_data)

    group_id = data.get("id")
    if not group_id:
        raise HTTPException(status_code=400, detail="ID de grupo requerido")

    try:
        async with pg_manager.get_session() as session:
            stmt = (
                select(TranslatorsGroup)
                .options(selectinload(TranslatorsGroup.contact_links))
                .where(TranslatorsGroup.id == int(group_id))
            )
            res = await session.execute(stmt)
            group = res.scalar_one_or_none()
            if not group:
                raise HTTPException(status_code=404, detail="Grupo no encontrado")

            # Buscar libros vinculados
            # 1. Por columnas directas (translator_group_id, editor_group_id, layout_group_id)
            # 2. O por la tabla asociativa BookWorkgroup
            book_stmt = (
                select(LocalBook)
                .where(
                    (LocalBook.translator_group_id == group.id)
                    | (LocalBook.editor_group_id == group.id)
                    | (LocalBook.layout_group_id == group.id)
                )
                .order_by(LocalBook.title.asc())
            )
            book_res = await session.execute(book_stmt)
            direct_books = book_res.scalars().all()

            # Asociativos
            bw_stmt = (
                select(BookWorkgroup)
                .options(selectinload(BookWorkgroup.book))
                .where(BookWorkgroup.workgroup_id == group.id)
            )
            bw_res = await session.execute(bw_stmt)
            bw_list = bw_res.scalars().all()

            books_map: dict[str, dict[str, Any]] = {}
            for b in direct_books:
                role = (
                    "translator"
                    if b.translator_group_id == group.id
                    else ("editor" if b.editor_group_id == group.id else "layout")
                )
                cover = (
                    getattr(b, "cover_low", None)
                    or getattr(b, "cover_medium", None)
                    or getattr(b, "cover_thumb", None)
                    or getattr(b, "cover_url", None)
                )
                epub_pub = getattr(b, "publisher", None)
                has_bad, issue = check_epub_metadata_issue(epub_pub, group.name)
                books_map[b.id] = {
                    "id": b.id,
                    "title": b.title or "Sin título",
                    "spanish_title": getattr(b, "spanish_title", None),
                    "english_title": getattr(b, "english_title", None),
                    "series_spanish": getattr(b, "series_spanish", None),
                    "series_id": getattr(b, "series_id", None),
                    "author": getattr(b, "author", None),
                    "publisher": epub_pub,
                    "filepath": getattr(b, "filepath", None),
                    "filename": getattr(b, "filename", None),
                    "cover_low": cover,
                    "cover_thumb": cover,
                    "role": role,
                    "volume": getattr(b, "volume", None),
                    "has_bad_metadata": has_bad,
                    "metadata_issue": issue,
                }

            for bw in bw_list:
                if bw.book and bw.book.id not in books_map:
                    bk = bw.book
                    cover = (
                        getattr(bk, "cover_low", None)
                        or getattr(bk, "cover_medium", None)
                        or getattr(bk, "cover_thumb", None)
                        or getattr(bk, "cover_url", None)
                    )
                    epub_pub = getattr(bk, "publisher", None)
                    has_bad, issue = check_epub_metadata_issue(epub_pub, group.name)
                    books_map[bk.id] = {
                        "id": bk.id,
                        "title": bk.title or "Sin título",
                        "spanish_title": getattr(bk, "spanish_title", None),
                        "english_title": getattr(bk, "english_title", None),
                        "series_spanish": getattr(bk, "series_spanish", None),
                        "series_id": getattr(bk, "series_id", None),
                        "author": getattr(bk, "author", None),
                        "publisher": epub_pub,
                        "filepath": getattr(bk, "filepath", None),
                        "filename": getattr(bk, "filename", None),
                        "cover_low": cover,
                        "cover_thumb": cover,
                        "role": bw.role or "translator",
                        "volume": getattr(bk, "volume", None),
                        "has_bad_metadata": has_bad,
                        "metadata_issue": issue,
                    }

            books_list = list(books_map.values())
            bad_count = sum(1 for bk in books_list if bk.get("has_bad_metadata"))
            good_count = len(books_list) - bad_count

            return {
                "group": {
                    "id": group.id,
                    "name": group.name,
                    "siglas": group.siglas,
                    "description": group.description,
                    "preferred_link": group.get_preferred_link(),
                    "links": group.get_links_dict(),
                    "books_count": len(books_list),
                    "bad_metadata_count": bad_count,
                    "good_metadata_count": good_count,
                    "created_at": group.created_at.isoformat()
                    if group.created_at
                    else None,
                },
                "books": books_list,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en handle_workgroup_get_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_workgroup_attach_book(data: dict[str, Any], user_data: dict[str, Any]):
    """Vincula un libro a un grupo traductor con un rol determinado."""
    check_staff(user_data)

    group_id = data.get("group_id")
    book_id = data.get("book_id")
    role = data.get("role", "translator")

    if not group_id or not book_id:
        raise HTTPException(status_code=400, detail="group_id y book_id requeridos")

    try:
        success = await WorkgroupService.assign_workgroup_to_book(
            book_id=str(book_id), workgroup_id=int(group_id), role=role
        )
        return {"success": success}
    except Exception as e:
        logger.error(f"Error vinculando libro {book_id} a grupo {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_workgroup_detach_book(data: dict[str, Any], user_data: dict[str, Any]):
    """Desvincula un libro de un grupo traductor."""
    check_staff(user_data)

    group_id = data.get("group_id")
    book_id = data.get("book_id")

    if not group_id or not book_id:
        raise HTTPException(status_code=400, detail="group_id y book_id requeridos")

    try:
        async with pg_manager.get_session() as session:
            # 1. Quitar de BookWorkgroup
            await session.execute(
                delete(BookWorkgroup).where(
                    BookWorkgroup.workgroup_id == int(group_id),
                    BookWorkgroup.book_id == str(book_id),
                )
            )
            # 2. Desvincular de columnas de LocalBook si coincide
            from models.library import Book

            b_stmt = select(Book).where(Book.id == str(book_id))
            b_res = await session.execute(b_stmt)
            book = b_res.scalar_one_or_none()
            if book:
                if book.translator_group_id == int(group_id):
                    book.translator_group_id = None
                if book.editor_group_id == int(group_id):
                    book.editor_group_id = None
                if book.layout_group_id == int(group_id):
                    book.layout_group_id = None

            await session.commit()
            logger.info(f"✅ Libro {book_id} desvinculado del grupo {group_id}")
            return {"success": True}
    except Exception as e:
        logger.error(f"Error desvinculando libro {book_id} de grupo {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_workgroup_merge(data: dict[str, Any], user_data: dict[str, Any]):
    """
    Fusiona uno o varios grupos traductores fuente dentro de un grupo traductor canónico de destino.
    Reasigna todos los libros (translator, editor, layout y BookWorkgroup), consolida enlaces
    y elimina los grupos fuente redundantes.
    """
    check_admin(user_data)

    target_id_raw = data.get("target_id")
    source_ids_raw = data.get("source_ids")

    if not target_id_raw:
        raise HTTPException(status_code=400, detail="target_id requerido")
    try:
        target_id = int(target_id_raw)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="target_id inválido")

    if not source_ids_raw:
        raise HTTPException(
            status_code=400, detail="source_ids requerido (lista de IDs a fusionar)"
        )

    if isinstance(source_ids_raw, (int, str)):
        source_ids = [int(source_ids_raw)]
    elif isinstance(source_ids_raw, list):
        source_ids = [int(x) for x in source_ids_raw if x is not None]
    else:
        raise HTTPException(
            status_code=400, detail="Formato de source_ids no soportado"
        )

    source_ids = [sid for sid in set(source_ids) if sid != target_id]
    if not source_ids:
        raise HTTPException(
            status_code=400,
            detail="Debe especificar al menos un grupo fuente distinto del destino",
        )

    try:
        async with pg_manager.get_session() as session:
            # 1. Obtener grupo destino
            stmt_target = (
                select(TranslatorsGroup)
                .options(selectinload(TranslatorsGroup.contact_links))
                .where(TranslatorsGroup.id == target_id)
            )
            res_target = await session.execute(stmt_target)
            target_group = res_target.scalar_one_or_none()
            if not target_group:
                raise HTTPException(
                    status_code=404, detail="Grupo canónico destino no encontrado"
                )

            # 2. Obtener grupos fuente
            stmt_sources = (
                select(TranslatorsGroup)
                .options(selectinload(TranslatorsGroup.contact_links))
                .where(TranslatorsGroup.id.in_(source_ids))
            )
            res_sources = await session.execute(stmt_sources)
            sources = res_sources.scalars().all()
            if not sources:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontraron los grupos fuente especificados",
                )

            found_source_ids = [s.id for s in sources]

            # 3. Reasignar libros directos (LocalBook)
            res_trans = await session.execute(
                update(LocalBook)
                .where(LocalBook.translator_group_id.in_(found_source_ids))
                .values(translator_group_id=target_id)
            )
            res_edit = await session.execute(
                update(LocalBook)
                .where(LocalBook.editor_group_id.in_(found_source_ids))
                .values(editor_group_id=target_id)
            )
            res_layout = await session.execute(
                update(LocalBook)
                .where(LocalBook.layout_group_id.in_(found_source_ids))
                .values(layout_group_id=target_id)
            )
            total_reassigned = (
                (res_trans.rowcount or 0)
                + (res_edit.rowcount or 0)
                + (res_layout.rowcount or 0)
            )

            # 4. Reasignar BookWorkgroup evitando colisiones de clave única
            existing_bw_res = await session.execute(
                select(BookWorkgroup.book_id, BookWorkgroup.role).where(
                    BookWorkgroup.workgroup_id == target_id
                )
            )
            existing_bw_keys = set(existing_bw_res.all())

            source_bw_res = await session.execute(
                select(BookWorkgroup).where(
                    BookWorkgroup.workgroup_id.in_(found_source_ids)
                )
            )
            source_bw_list = source_bw_res.scalars().all()

            for bw in source_bw_list:
                key = (bw.book_id, bw.role)
                if key in existing_bw_keys:
                    await session.delete(bw)
                else:
                    bw.workgroup_id = target_id
                    existing_bw_keys.add(key)

            # 5. Consolidar metadatos y enlaces si destino carece de ellos
            if not target_group.siglas:
                for s in sources:
                    if s.siglas:
                        target_group.siglas = s.siglas
                        break
            if not target_group.description:
                for s in sources:
                    if s.description:
                        target_group.description = s.description
                        break

            target_platforms = {
                cl.platform.lower(): cl
                for cl in target_group.contact_links
                if cl.platform
            }
            for s in sources:
                for cl in s.contact_links:
                    plat = (cl.platform or "").lower()
                    if plat and plat not in target_platforms and cl.url:
                        new_link = GroupContactLink(
                            group_id=target_id, platform=plat, url=cl.url
                        )
                        session.add(new_link)
                        target_platforms[plat] = new_link

            # 6. Eliminar grupos fuente absorbidos
            for s in sources:
                await session.execute(
                    delete(GroupContactLink).where(GroupContactLink.group_id == s.id)
                )
                await session.delete(s)

            await session.commit()

            logger.info(
                f"🔀 Fusión completada: {len(sources)} grupos {found_source_ids} absorbidos en '{target_group.name}' (#{target_id}). "
                f"{total_reassigned} libros reasignados."
            )

            return {
                "success": True,
                "target_id": target_id,
                "target_name": target_group.name,
                "merged_count": len(sources),
                "merged_ids": found_source_ids,
                "books_reassigned": total_reassigned,
                "message": f"Se fusionaron {len(sources)} grupo(s) con éxito en '{target_group.name}'.",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en handle_workgroup_merge: {e}")
        raise HTTPException(status_code=500, detail=str(e))
