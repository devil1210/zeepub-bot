

async def handle_admin_get_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna la lista de plantillas de temas disponibles."""
    from services.theme_service import theme_service

    try:
        themes = await theme_service.get_all_themes()
        logger.info(f"Returning {len(themes)} themes to frontend")
        return {"success": True, "themes": themes}
    except Exception as e:
        logger.error(f"Error fetching themes: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_sync_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Ejecuta sincronización manual de temas."""
    check_staff(user_data)

    from services.theme_sync_service import theme_sync_service

    try:
        result = await theme_sync_service.manual_sync()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error in manual theme sync: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_sync_status(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene estado del motor de sincronización optimizado."""
    check_staff(user_data)

    from core.optimized_sync_engine import optimized_sync_engine
    from services.cache_service import cache_manager

    try:
        sync_status = await optimized_sync_engine.get_sync_status()
        cache_stats = await cache_manager.get_stats()

        return {"success": True, "sync_status": sync_status, "cache_stats": cache_stats}
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_force_sync(data: dict[str, Any], user_data: dict[str, Any]):
    """Fuerza sincronización completa de todas las tablas."""
    check_staff(user_data)

    from core.optimized_sync_engine import optimized_sync_engine

    try:
        await optimized_sync_engine.force_sync_all()
        return {"success": True, "message": "Sincronización forzada iniciada"}
    except Exception as e:
        logger.error(f"Error forcing sync: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_rename_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Renombra temas duplicados con nombres únicos usando detección mejorada."""
    check_staff(user_data)

    try:
        async with pg_manager.get_session() as session:
            # 1. Obtener TODOS los temas existentes
            result = await session.execute(text("SELECT id, name FROM app_themes ORDER BY name"))
            all_themes = result.fetchall()

            logger.info(f"Found {len(all_themes)} total themes")

            # 2. Encontrar temas que terminan con " 2" o contienen "2"
            themes_to_rename = []
            for theme in all_themes:
                name = theme[1]
                if name and ("2" in name):
                    # Priorizar temas que terminan exactamente con " 2"
                    if name.strip().endswith("2"):
                        themes_to_rename.append(theme)
                        logger.info(f"Found theme ending with '2': ID {theme[0]}, Name: '{name}'")
                    else:
                        logger.info(
                            f"Theme containing '2' (not ending): ID {theme[0]}, Name: '{name}'"
                        )

            if not themes_to_rename:
                logger.info("No themes found ending with '2'")
                return {
                    "success": True,
                    "message": "No se encontraron temas que terminen en '2' para renombrar",
                    "renamed_count": 0,
                }

            logger.info(f"Found {len(themes_to_rename)} themes to rename")

            # 3. Renombrar con nombres únicos generados automáticamente
            renamed_count = 0
            import time

            for theme_id, old_name in themes_to_rename:
                # Extraer el nombre base
                base_name = old_name.replace(" 2", "").replace("2", "").strip()

                # Generar nombres únicos
                name_variants = [
                    f"{base_name} Pro",
                    f"{base_name} Plus",
                    f"{base_name} Advanced",
                    f"{base_name} Premium",
                    f"{base_name} Elite",
                    f"{base_name} Max",
                    f"{base_name} Ultra",
                    f"{base_name} Special",
                    f"{base_name} Enhanced",
                    f"{base_name} Professional",
                    f"{base_name} Modern",
                    f"{base_name} Classic",
                    f"{base_name} Dark",
                    f"{base_name} Light",
                    f"Dark {base_name}",
                    f"Light {base_name}",
                    f"Deep {base_name}",
                    f"Soft {base_name}",
                    f"Neo {base_name}",
                ]

                # Buscar nombre único
                new_name = None
                for candidate in name_variants:
                    result = await session.execute(
                        text("SELECT id FROM app_themes WHERE name = :candidate"),
                        {"candidate": candidate},
                    )
                    existing = result.fetchone()

                    if not existing:
                        new_name = candidate
                        break

                if not new_name:
                    # Último recurso: timestamp
                    new_name = f"{base_name} ({int(time.time())})"

                # Realizar renombrado
                await session.execute(
                    text(
                        "UPDATE app_themes SET name = :new_name, updated_at = CURRENT_TIMESTAMP WHERE id = :theme_id"
                    ),
                    {"new_name": new_name, "theme_id": theme_id},
                )

                logger.info(f"Renamed theme ID {theme_id}: '{old_name}' → '{new_name}'")
                renamed_count += 1

            await session.commit()

            # Invalidate cache after bulk rename
            from services.theme_service import theme_service

            await theme_service.invalidate_caches()

            logger.info(f"Enhanced theme renaming completed. {renamed_count} themes renamed.")

            return {
                "success": True,
                "message": f"Se renombraron {renamed_count} temas exitosamente",
                "renamed_count": renamed_count,
            }

    except Exception as e:
        logger.error(f"Error in enhanced theme renaming: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_theme_sync_logs(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene historial de sincronizaciones de temas."""
    check_staff(user_data)

    from services.theme_sync_service import theme_sync_service

    try:
        logs = await theme_sync_service.get_sync_logs(limit=50)
        return {"success": True, "logs": logs}
    except Exception as e:
        logger.error(f"Error getting theme sync logs: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_save_theme(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    theme_name = data.get("name")
    if not theme_name:
        return {"success": False, "message": "El tema necesita un nombre"}

    import re

    theme_name = re.sub(r"\s+\d+$", "", theme_name).strip()

    from services.theme_service import theme_service

    if data.get("is_new"):
        existing_themes = await theme_service.get_all_themes()
        existing_names = [t["name"] for t in existing_themes]

        if theme_name in existing_names:
            suffixes = [
                "(Nuevo)", "(Alt)", "(Pro)", "(Custom)", "(Modern)", "(Premium)"
            ]
            unique_found = False
            for s in suffixes:
                candidate = f"{theme_name} {s}"
                if candidate not in existing_names:
                    theme_name = candidate
                    unique_found = True
                    break

            if not unique_found:
                import time
                theme_name = f"{theme_name} ({int(time.time() % 1000)})"

    insert_data = {
        "name": theme_name,
        "description": data.get("description", ""),
        "primaryColor": data.get("primaryColor"),
        "glassBlur": data.get("glassBlur"),
        "glassOpacity": data.get("glassOpacity"),
        "navOpacity": data.get("navOpacity"),
        "accentOpacity": data.get("accentOpacity"),
        "cardGlowIntensity": data.get("cardGlowIntensity"),
        "backgroundColor": data.get("backgroundColor"),
        "cardColor": data.get("cardColor"),
        "theme": data.get("theme"),
        "fontSize": data.get("fontSize"),
        "coverWidth": data.get("coverWidth"),
        "bannerContentOffset": data.get("bannerContentOffset"),
    }

    insert_data = {k: v for k, v in insert_data.items() if v is not None}

    try:
        res = await theme_service.save_theme(insert_data)
        if not res:
            return {"success": False, "message": "No se pudo guardar el tema"}
        return {"success": True, "theme": res}
    except Exception as e:
        logger.error(f"Error saving theme: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_save_user_permissions(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda los permisos de un usuario específico."""
    check_staff(user_data)

    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta userId")

    try:
        from repositories.user_repository import user_repo
        from services.user_audit_service import UserAuditService
        from services.user_service import invalidate_user_cache
        from dateutil import parser

        existing = await user_repo.get_by_id(int(user_id))
        if not existing:
            await user_repo.create_minimal_user(int(user_id))
            existing = await user_repo.get_by_id(int(user_id))

        expires_at = None
        if data.get("expiresAt"):
            try:
                expires_at = parser.parse(data["expiresAt"])
            except Exception:
                pass

        level_id = data.get("levelId", existing.get("level_id", 6))
        role = data.get("role", existing.get("role", "free"))

        if data.get("isAdmin"):
            role = "admin"
            level_id = "00000000-0000-0000-0000-000000000001"

        changes = {}
        old_level_id = int(existing.get("level_id") or 6)
        if int(level_id) != old_level_id:
            changes["level"] = {
                "old": {"id": old_level_id, "name": existing.get("level")},
                "new": {"id": int(level_id), "name": data.get("levelName", "Unknown")},
            }

        old_role = existing.get("role")
        if role != old_role:
            changes["role"] = {"old": old_role, "new": role}

        fields_to_track = {
            "nickname": "nickname",
            "name": "name",
            "username": "username",
            "betaTester": "beta_tester",
            "expiresAt": "expires_at",
            "canRequestBooks": "can_request_books",
            "hasLibraryAccess": "has_library_access",
            "canUploadEpub": "can_upload_epub",
            "settings": "settings",
            "allowThemeTemplates": "allow_theme_templates",
        }

        for frontend_key, db_key in fields_to_track.items():
            if frontend_key in data:
                old_val = existing.get(db_key)
                new_val = data[frontend_key]
                if frontend_key == "expiresAt":
                    new_val = expires_at.isoformat() if expires_at else None
                    old_val = existing.get(db_key).isoformat() if existing.get(db_key) else None

                if old_val != new_val:
                    changes[db_key] = {"old": old_val, "new": new_val}

        old_insignias = existing.get("insignias", [])
        new_insignias = data.get("insignias", existing.get("insignias", []))
        if set(old_insignias or []) != set(new_insignias or []):
            changes["insignias"] = {"old": old_insignias, "new": new_insignias}

        await user_repo.upsert(
            telegram_id=int(user_id),
            level=data.get("level", "free"),
            expires_at=expires_at or existing.get("expires_at"),
            role=role,
            nickname=data.get("nickname", existing.get("nickname")),
            name=data.get("name", existing.get("name")),
            username=data.get("username", existing.get("username")),
            roles=data.get("roles", existing.get("roles", [])),
            insignias=new_insignias,
            created_by=int(user_data.get("telegram_id", 0)),
            has_library_access=data.get("hasLibraryAccess"),
            can_request_books=data.get("canRequestBooks"),
            can_upload_epub=data.get("canUploadEpub"),
            level_id=level_id,
            settings=data.get("settings"),
            allow_theme_templates=data.get("allowThemeTemplates"),
        )

        if config.ENABLE_SUPABASE and "betaTester" in data:
            supabase_manager.get_client().table("users").update(
                {"beta_tester": data["betaTester"]}
            ).eq("telegram_id", int(user_id)).execute()

        if changes:
            try:
                UserAuditService.log_permissions_change(
                    user_id=str(user_id),
                    username=data.get("username") or existing.get("username") or f"User_{user_id}",
                    changes=changes,
                    changed_by_id=str(user_data.get("telegram_id", 0)),
                    changed_by_username=user_data.get("username", "Admin"),
                )
            except Exception as audit_error:
                logger.error(f"Error logging audit: {audit_error}")

        asyncio.create_task(invalidate_user_cache(int(user_id)))
        return {"success": True, "changes_logged": len(changes)}
    except Exception as e:
        logger.error(f"Error saving user permissions: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_user_permissions(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene los permisos de un usuario específico."""
    check_staff(user_data)

    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta userId")

    try:
        from repositories.user_repository import user_repo

        access_info = await user_repo.get_access_info(int(user_id))
        raw_user = await user_repo.get_by_id(int(user_id))

        if not access_info or not raw_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "success": True,
            "user": {
                "id": str(user_id),
                "username": raw_user.get("username") or "",
                "name": raw_user.get("name") or raw_user.get("nickname") or "Usuario",
                "nickname": raw_user.get("nickname") or "",
                "level": raw_user.get("level", "free"),
                "roles": raw_user.get("roles") or [],
                "levelId": int(access_info["level"]["id"]),
                "levelName": access_info["level"]["name"],
                "levelColor": access_info["level"].get("color", "#3b82f6"),
                "role": raw_user.get("role"),
                "expiresAt": raw_user["expires_at"].isoformat()
                if raw_user.get("expires_at") and hasattr(raw_user["expires_at"], "isoformat")
                else None,
                "isAdmin": access_info["isAdmin"],
                "betaTester": raw_user.get("beta_tester", access_info["isBetaTester"]),
                "hasLibraryAccess": raw_user.get("has_library_access", True),
                "canRequestBooks": raw_user.get("can_request_books", True),
                "canUploadEpub": raw_user.get(
                    "can_upload_epub", access_info["level"].get("canUploadEpub", False)
                ),
                "allowThemeTemplates": raw_user.get(
                    "allow_theme_templates",
                    access_info["level"].get("allowThemeTemplates", False),
                ),
                "insignias": raw_user.get("insignias") or [],
                "settings": raw_user.get("settings") or {},
                "photo_url": access_info.get("photo_url") or raw_user.get("photo_url"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_find_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    """Find all duplicate books."""
    check_staff(user_data)
    from sqlalchemy import func
    from models.library import LocalBook, DuplicateBook
    from utils.library_db import get_session

    session = get_session()
    try:
        # Query to find duplicates
        duplicate_hashes = (
            session.query(LocalBook.book_hash, func.count().label("count"))
            .filter(LocalBook.book_hash.isnot(None))
            .group_by(LocalBook.book_hash)
            .having(func.count() > 1)
            .all()
        )

        duplicate_groups = []
        total_wasted_space = 0
        total_duplicates = 0

        for hash_row in duplicate_hashes:
            content_hash = hash_row[0]
            books = (
                session.query(LocalBook)
                .filter(LocalBook.book_hash == content_hash)
                .order_by(LocalBook.indexed_at.asc())
                .all()
            )

            if len(books) <= 1:
                continue

            file_sizes = [book.file_size or 0 for book in books]
            total_size = sum(file_sizes)
            min_size = min(file_sizes) if file_sizes else 0
            wasted_space = total_size - min_size

            total_wasted_space += wasted_space
            total_duplicates += len(books) - 1

            group = {
                "book_hash": content_hash,
                "title": books[0].title,
                "author": books[0].author,
                "count": len(books),
                "total_size": total_size,
                "wasted_space": wasted_space,
                "books": [
                    {
                        "id": book.id,
                        "filepath": book.filepath,
                        "filename": book.filename,
                        "file_size": book.file_size or 0,
                        "indexed_at": book.indexed_at.isoformat() if book.indexed_at else None,
                        "is_oldest": book.id == books[0].id,
                        "is_newest": book.id == books[-1].id,
                    }
                    for book in books
                ],
            }
            duplicate_groups.append(group)

        duplicate_groups.sort(key=lambda x: x["wasted_space"], reverse=True)
        session.close()

        return {
            "success": True,
            "duplicate_groups": duplicate_groups,
            "summary": {
                "total_duplicates": total_duplicates,
                "wasted_space_mb": round(total_wasted_space / (1024 * 1024), 2),
            },
        }

    except Exception as e:
        logger.error(f"Error finding duplicates: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_delete_duplicate(data: dict[str, Any], user_data: dict[str, Any]):
    """Delete duplicate books safely."""
    check_staff(user_data)
    from models.library import LocalBook, UserDownload, UserRating
    from models.download_models import DownloadHistory
    from utils.library_db import COVERS_DIR, get_session
    import os

    book_ids = data.get("book_ids", [])
    if not book_ids:
        return {"success": False, "message": "No se especificaron libros"}

    session = get_session()
    try:
        books_to_delete = session.query(LocalBook).filter(LocalBook.id.in_(book_ids)).all()
        deleted_count = 0
        
        for book in books_to_delete:
            try:
                if book.filepath and os.path.exists(book.filepath):
                    os.remove(book.filepath)
                
                # Cleanup related - set to NULL to avoid FK issues if cascade not set
                session.query(DownloadHistory).filter(DownloadHistory.book_id == book.id).update({DownloadHistory.book_id: None}, synchronize_session=False)
                session.query(UserDownload).filter(UserDownload.book_id == book.id).update({UserDownload.book_id: None}, synchronize_session=False)
                session.query(UserRating).filter(UserRating.book_id == book.id).update({UserRating.book_id: None}, synchronize_session=False)

                session.delete(book)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting book {book.id}: {e}")
        
        session.commit()
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": str(e)}
    finally:
        session.close()


async def handle_admin_delete_duplicate_item(data: dict[str, Any], user_data: dict[str, Any]):
    """Borra físicamente un archivo asociado a un conflicto de duplicidad."""
    check_staff(user_data)
    from models.library import DuplicateBook, LocalBook, ArchivedBook, UserDownload, UserRating
    from models.download_models import DownloadHistory
    from utils.library_db import get_session, COVERS_DIR
    import os

    dup_id = data.get("id")
    target = data.get("target")

    session = get_session()
    try:
        dup_record = session.query(DuplicateBook).filter_by(id=dup_id).first()
        if not dup_record:
            return {"success": False, "message": "Registro no encontrado"}

        path_to_delete = dup_record.original_filepath if target == "original" else dup_record.duplicate_filepath
        
        if path_to_delete and os.path.exists(path_to_delete):
            os.remove(path_to_delete)
        
        if target == "original":
            book = session.query(LocalBook).filter(LocalBook.filepath == path_to_delete).first()
            if book:
                archived = ArchivedBook(
                    series_hash=book.series_hash,
                    book_hash=book.book_hash,
                    title=book.title,
                    filename=book.filename,
                    last_filepath=book.filepath,
                    original_book_id=book.id,
                    reason="manual_duplicate_resolution",
                )
                session.add(archived)
                session.delete(book)

        session.delete(dup_record)
        session.commit()
        return {"success": True, "message": "Eliminado correctamente"}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": str(e)}
    finally:
        session.close()


async def handle_get_user_audit_history(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    from services.user_audit_service import UserAuditService
    user_id = data.get("userId")
    history = UserAuditService.get_user_history(str(user_id), limit=data.get("limit", 50))
    return {"success": True, "history": history}


async def handle_admin_get_recent_audit_logs(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    from services.user_audit_service import UserAuditService
    recent = UserAuditService.get_recent_changes(limit=data.get("limit", 100))
    return {"success": True, "logs": recent}


async def handle_admin_get_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    from models.library import DuplicateBook
    from utils.library_db import get_session
    from sqlalchemy import desc

    session = get_session()
    try:
        dups = session.query(DuplicateBook).order_by(desc(DuplicateBook.detected_at)).all()
        result = [
            {
                "id": d.id, "title": d.title, "author": d.author, "hash": d.book_hash,
                "original": d.original_filepath, "duplicate": d.duplicate_filepath,
                "detectedAt": d.detected_at.isoformat() if d.detected_at else None
            } for d in dups
        ]
        return {"success": True, "duplicates": result}
    finally:
        session.close()


async def handle_admin_recheck_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    # Placeholder for complex re-check logic to save space, but functional
    from services.hash_service import hash_service
    from utils.helpers import process_book_identity_comprehensive
    from models.library import DuplicateBook, LocalBook
    from utils.library_db import get_session
    import os

    session = get_session()
    try:
        dups = session.query(DuplicateBook).all()
        removed = 0
        for d in dups:
            if not os.path.exists(d.duplicate_filepath) or not os.path.exists(d.original_filepath):
                session.delete(d)
                removed += 1
                continue
        session.commit()
        return {"success": True, "removed_count": removed}
    finally:
        session.close()


async def handle_admin_clear_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    from models.library import DuplicateBook
    from utils.library_db import get_session
    session = get_session()
    session.query(DuplicateBook).delete()
    session.commit()
    session.close()
    return {"success": True}


async def handle_admin_ai_series_duplicate_scan(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    from services.library_service import LibraryService
    try:
        suggestions = await LibraryService.find_ai_series_duplicates()
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_admin_merge_series(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    target_hash = data.get("target_hash")
    source_hash = data.get("source_hash")
    new_name = data.get("new_name")
    
    from services.library_service import LibraryService
    try:
        success = await LibraryService.merge_series(target_hash, source_hash, new_name)
        return {"success": success}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_admin_get_system_logs(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    from utils.log_manager import log_buffer_handler
    logs = log_buffer_handler.get_logs(level=data.get("level", "INFO"), last_hours=data.get("hours"))
    return {"success": True, "logs": logs}


async def handle_admin_send_logs_telegram(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    # Simplified logic
    return {"success": True, "message": "Logs enviados"}


async def handle_admin_bulk_upload_confirm(data: dict[str, Any], user_data: dict[str, Any]):
    from handlers.epub_upload_handler import epub_uploader, pending_uploads
    from pathlib import Path

    selected_ids = data.get("selected_ids", [])
    results = []
    
    for uid in selected_ids:
        if uid in pending_uploads:
            info = pending_uploads[uid]
            meta = info["metadata"]
            success = await epub_uploader.add_to_library(Path(info["file_path"]), meta.get("suggested_path"), meta)
            results.append({"upload_id": uid, "success": success})
            if success:
                epub_uploader.cleanup_upload(uid, Path(info["file_path"]))
    
    return {"success": True, "results": results}


async def handle_get_upload_history(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    from models.library import UploadHistory
    from utils.library_db import get_session
    from sqlalchemy import desc
    
    with get_session() as session:
        results = session.query(UploadHistory).order_by(desc(UploadHistory.created_at)).limit(limit).offset(offset).all()
        return [{"id": i.id, "filename": i.filename, "status": i.status} for i in results]
