import logging
from typing import Any
from fastapi import HTTPException
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from api.handlers.helpers import check_admin, check_staff
from core.db_manager_pg import pg_manager
from models.library import TranslatorsGroup, GroupContactLink, LocalBook, BookWorkgroup
from services.workgroup_service import WorkgroupService

logger = logging.getLogger(__name__)


async def handle_workgroup_get_all(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna la lista completa de grupos traductores con sus enlaces y estadísticas."""
    check_staff(user_data)
    
    try:
        async with pg_manager.get_session() as session:
            stmt = select(TranslatorsGroup).options(
                selectinload(TranslatorsGroup.contact_links)
            ).order_by(TranslatorsGroup.name.asc())
            
            res = await session.execute(stmt)
            groups = res.scalars().all()
            
            # Obtener conteo de libros asociados a cada grupo
            count_stmt = select(
                LocalBook.translator_group_id,
                func.count(LocalBook.id)
            ).group_by(LocalBook.translator_group_id)
            count_res = await session.execute(count_stmt)
            counts_map = {row[0]: row[1] for row in count_res.all() if row[0] is not None}
            
            result = []
            for g in groups:
                links_dict = g.get_links_dict()
                result.append({
                    "id": g.id,
                    "name": g.name,
                    "siglas": g.siglas,
                    "description": g.description,
                    "preferred_link": g.get_preferred_link(),
                    "books_count": counts_map.get(g.id, 0),
                    "links": links_dict,
                    "created_at": g.created_at.isoformat() if g.created_at else None,
                })
                
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
        raise HTTPException(status_code=400, detail="El nombre del grupo es obligatorio")
        
    try:
        async with pg_manager.get_session() as session:
            if group_id:
                stmt = select(TranslatorsGroup).options(
                    selectinload(TranslatorsGroup.contact_links)
                ).where(TranslatorsGroup.id == int(group_id))
                res = await session.execute(stmt)
                group = res.scalar_one_or_none()
                if not group:
                    raise HTTPException(status_code=404, detail="Grupo no encontrado")
                group.name = name
                group.siglas = siglas
                group.description = description
            else:
                group = TranslatorsGroup(name=name, siglas=siglas, description=description)
                session.add(group)
                await session.flush()
                await session.refresh(group)
                
            # Actualizar enlaces de contacto
            valid_platforms = ["web", "fb", "discord", "patreon", "twitter", "donations"]
            for plat in valid_platforms:
                url_val = (links.get(plat) or "").strip()
                link_stmt = select(GroupContactLink).where(
                    GroupContactLink.group_id == group.id,
                    func.lower(GroupContactLink.platform) == plat
                )
                link_res = await session.execute(link_stmt)
                existing_link = link_res.scalar_one_or_none()
                
                if url_val:
                    if existing_link:
                        existing_link.url = url_val
                    else:
                        new_link = GroupContactLink(group_id=group.id, platform=plat, url=url_val)
                        session.add(new_link)
                elif existing_link:
                    await session.delete(existing_link)
                    
            await session.commit()
            logger.info(f"✅ Grupo traductor guardado exitosamente: {name} (ID: {group.id})")
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
                update(LocalBook).where(LocalBook.translator_group_id == int(group_id)).values(translator_group_id=None)
            )
            await session.execute(
                update(LocalBook).where(LocalBook.editor_group_id == int(group_id)).values(editor_group_id=None)
            )
            await session.execute(
                update(LocalBook).where(LocalBook.layout_group_id == int(group_id)).values(layout_group_id=None)
            )
            
            # 2. Eliminar de BookWorkgroup
            await session.execute(
                delete(BookWorkgroup).where(BookWorkgroup.workgroup_id == int(group_id))
            )
            
            # 3. Eliminar grupo (links se eliminan por cascade)
            del_stmt = delete(TranslatorsGroup).where(TranslatorsGroup.id == int(group_id))
            await session.execute(del_stmt)
            await session.commit()
            
            logger.info(f"🗑️ Grupo traductor {group_id} eliminado exitosamente")
            return {"success": True, "deleted_id": group_id}
    except Exception as e:
        logger.error(f"Error en handle_workgroup_delete: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_workgroup_get_detail(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna los datos completos de un fansub/grupo y todos los libros EPUB vinculados a él."""
    check_staff(user_data)
    
    group_id = data.get("id")
    if not group_id:
        raise HTTPException(status_code=400, detail="ID de grupo requerido")
        
    try:
        async with pg_manager.get_session() as session:
            stmt = select(TranslatorsGroup).options(
                selectinload(TranslatorsGroup.contact_links)
            ).where(TranslatorsGroup.id == int(group_id))
            res = await session.execute(stmt)
            group = res.scalar_one_or_none()
            if not group:
                raise HTTPException(status_code=404, detail="Grupo no encontrado")
                
            # Buscar libros vinculados
            # 1. Por columnas directas (translator_group_id, editor_group_id, layout_group_id)
            # 2. O por la tabla asociativa BookWorkgroup
            book_stmt = select(LocalBook).where(
                (LocalBook.translator_group_id == group.id) |
                (LocalBook.editor_group_id == group.id) |
                (LocalBook.layout_group_id == group.id)
            ).order_by(LocalBook.title.asc())
            book_res = await session.execute(book_stmt)
            direct_books = book_res.scalars().all()
            
            # Asociativos
            bw_stmt = select(BookWorkgroup).options(
                selectinload(BookWorkgroup.book)
            ).where(BookWorkgroup.workgroup_id == group.id)
            bw_res = await session.execute(bw_stmt)
            bw_list = bw_res.scalars().all()
            
            books_map: dict[str, dict[str, Any]] = {}
            for b in direct_books:
                role = "translator" if b.translator_group_id == group.id else ("editor" if b.editor_group_id == group.id else "layout")
                cover = getattr(b, "cover_low", None) or getattr(b, "cover_medium", None) or getattr(b, "cover_thumb", None) or getattr(b, "cover_url", None)
                books_map[b.id] = {
                    "id": b.id,
                    "title": b.title or "Sin título",
                    "spanish_title": getattr(b, "spanish_title", None),
                    "english_title": getattr(b, "english_title", None),
                    "author": getattr(b, "author", None),
                    "cover_low": cover,
                    "cover_thumb": cover,
                    "role": role,
                    "volume": getattr(b, "volume", None),
                }
                
            for bw in bw_list:
                if bw.book and bw.book.id not in books_map:
                    bk = bw.book
                    cover = getattr(bk, "cover_low", None) or getattr(bk, "cover_medium", None) or getattr(bk, "cover_thumb", None) or getattr(bk, "cover_url", None)
                    books_map[bk.id] = {
                        "id": bk.id,
                        "title": bk.title or "Sin título",
                        "spanish_title": getattr(bk, "spanish_title", None),
                        "english_title": getattr(bk, "english_title", None),
                        "author": getattr(bk, "author", None),
                        "cover_low": cover,
                        "cover_thumb": cover,
                        "role": bw.role or "translator",
                        "volume": getattr(bk, "volume", None),
                    }
                    
            return {
                "group": {
                    "id": group.id,
                    "name": group.name,
                    "siglas": group.siglas,
                    "description": group.description,
                    "preferred_link": group.get_preferred_link(),
                    "links": group.get_links_dict(),
                    "books_count": len(books_map),
                    "created_at": group.created_at.isoformat() if group.created_at else None,
                },
                "books": list(books_map.values())
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
            book_id=str(book_id),
            workgroup_id=int(group_id),
            role=role
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
                    BookWorkgroup.book_id == str(book_id)
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
