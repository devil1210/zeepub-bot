import asyncio
import json
import logging
import os
import shutil
import threading
import time
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc, func, or_, select, text

from api.handlers.helpers import check_staff
from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.library_models import DuplicateBook, LocalBook, UploadHistory
from repositories.user_repository import user_repo
from services.scanner_service import ScannerService
from services.settings_service import get_setting, set_setting
from services.sync_service import SyncService
from services.tier_service import tier_service

logger = logging.getLogger(__name__)


async def handle_admin_stats(data: dict[str, Any], user_data: dict[str, Any], request=None):
    """Calcula y devuelve estadísticas globales reales desde PostgreSQL para el Panel Admin."""
    check_staff(user_data)

    total_users = 0
    total_books = 0
    dls_24h = 0
    dls_prev_24h = 0
    users_7d = 0
    storage_gb = 0

    try:
        async with pg_manager.get_session() as session:
            # 1. Basic Counts
            total_users = (await session.execute(text("SELECT COUNT(*) FROM users"))).scalar() or 0
            total_books = (
                await session.execute(text("SELECT COUNT(*) FROM local_books"))
            ).scalar() or 0
            users_7d = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM users WHERE created_at >= (CURRENT_TIMESTAMP - INTERVAL '7 days')"
                    )
                )
            ).scalar() or 0

            # 2. Storage
            res_size = await session.execute(text("SELECT SUM(file_size) FROM local_books"))
            total_bytes = res_size.scalar() or 0
            storage_gb = round(total_bytes / (1024**3), 2)

            # 3. Download Metrics
            dls_24h = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM download_history WHERE downloaded_at >= (CURRENT_TIMESTAMP - INTERVAL '1 day')"
                    )
                )
            ).scalar() or 0
            dls_prev_24h = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM download_history WHERE downloaded_at >= (CURRENT_TIMESTAMP - INTERVAL '2 days') AND downloaded_at < (CURRENT_TIMESTAMP - INTERVAL '1 day')"
                    )
                )
            ).scalar() or 0

            # 4. Revenue Estimation (Real from levels)
            cursor = await session.execute(
                text("""
                SELECT ul.price, COUNT(u.telegram_id) 
                FROM user_levels ul
                LEFT JOIN users u ON u.level_id = ul.id
                GROUP BY ul.id, ul.price
            """)
            )
            tier_revenue = cursor.fetchall()
            total_revenue = sum((price or 0.0) * count for price, count in tier_revenue)
    except Exception as e:
        logger.error(f"Error fetching global stats from Postgres: {e}")
        total_revenue = 0

    # Calculate Uptime
    # Avoid circular import by accessing app state via request if provided, or fallback
    start_time = time.time()
    if request and hasattr(request.app.state, "start_time"):
        start_time = request.app.state.start_time
    elif hasattr(config, "start_time"):  # Fallback if set in config? No usually in app state.
        pass

    # We might need to import app_state from main if not passed in request
    # But for handlers called by route dispatch, we might pass request or not.
    # miniapp_handlers used: from api.main import app_state
    # We will do local import
    try:
        from api.main import app_state

        start_time = app_state.get("start_time", time.time())
    except ImportError:
        pass

    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_text = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

    # Active Sessions (via StateManager)
    from core.state_manager import state_manager

    active_sessions = len(state_manager.user_state)

    # 5. Popular Book (Last 30 days)
    popular_book = None
    try:
        async with pg_manager.get_session() as session:
            cursor = await session.execute(
                text("""
                SELECT title, clean_title, book_hash, COUNT(*) as dls
                FROM download_history 
                WHERE downloaded_at >= NOW() - INTERVAL '30 days'
                GROUP BY book_hash, title, clean_title
                ORDER BY dls DESC
                LIMIT 1
            """)
            )
            row = cursor.fetchone()
            if row:
                p_title, p_clean_title, p_book_hash, p_dls = row
                popular_book = {
                    "title": p_clean_title or p_title,
                    "downloads": p_dls,
                    "author": "N/A",
                }
                stmt_lb = select(LocalBook).where(
                    or_(LocalBook.book_hash == p_book_hash, LocalBook.title == p_title)
                )
                lb_res = await session.execute(stmt_lb)
                lb = lb_res.scalar_one_or_none()
                if lb:
                    popular_book["author"] = lb.author
                    popular_book["cover"] = lb.cover_low
    except Exception as e:
        logger.error(f"Error fetching popular book: {e}")

    return {
        "revenue": round(total_revenue, 2),
        "activeSessions": active_sessions,
        "storageUsedGB": storage_gb,
        "storageTotalGB": 1000,
        "popularBook": popular_book,
        "growthTrend": [
            {
                "date": "Semana 1",
                "users": total_users - users_7d,
                "downloads": dls_prev_24h,
            },
            {"date": "Semana 2", "users": total_users, "downloads": dls_24h},
        ],
        "totalUsers": total_users,
        "users7d": users_7d,
        "totalBooks": total_books,
        "downloads24h": dls_24h,
        "downloadsPrev24h": dls_prev_24h,
        "uptime": uptime_text,
    }


async def handle_admin_get_tiers(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene todos los niveles y su configuración."""
    check_staff(user_data)
    levels = await tier_service.get_all_tiers()
    logger.info(f"ADMIN: handle_admin_get_tiers found {len(levels)} levels")
    return {"success": True, "levels": levels, "tiers": levels}


async def handle_admin_save_tier(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda cambios en un nivel."""
    check_staff(user_data)
    level_id = data.get("id")
    if not level_id:
        raise HTTPException(status_code=400, detail="Falta level_id")
    await tier_service.update_tier(int(level_id), data)
    return {"success": True}


async def handle_admin_get_users(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene la lista paginada de usuarios para el panel admin."""
    check_staff(user_data)
    limit = data.get("limit", 20)
    offset = data.get("offset", 0)
    search = data.get("search")
    users = await user_repo.list_users(limit=limit, offset=offset, search=search)
    return {"users": users}


async def handle_admin_set_user_level(data: dict[str, Any], user_data: dict[str, Any]):
    """Cambia el nivel de un usuario específico."""
    check_staff(user_data)
    target_id = data.get("userId")
    level_id = data.get("levelId")
    if not target_id or not level_id:
        raise HTTPException(status_code=400, detail="Faltan parámetros userId o levelId")
    await user_repo.update_user_level(int(target_id), int(level_id))
    return {"success": True}


async def handle_admin_scan_user(data: dict[str, Any], user_data: dict[str, Any], request=None):
    """Sincroniza la foto de perfil de un usuario desde Telegram."""
    check_staff(user_data)
    target_id = data.get("userId")
    if not target_id:
        raise HTTPException(status_code=400, detail="Falta parámetro userId")

    bot = None
    if request and hasattr(request.app.state, "bot_instance"):
        bot = request.app.state.bot_instance.app.bot

    if not bot:
        # Try importing if request not available
        try:
            from api.main import bot as global_bot

            bot = global_bot
        except ImportError:
            return {"success": False, "message": "Bot instance no disponible"}

    from services.user_service import sync_user_profile_photo

    photo_url = await sync_user_profile_photo(int(target_id), bot)

    if photo_url:
        return {"success": True, "photo_url": photo_url}
    else:
        return {
            "success": False,
            "message": "No se pudo sincronizar la foto de perfil (el usuario puede no tener una o tenerla privada).",
        }


async def handle_admin_backup_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Syncs everything (Users, Levels, and Library) to Supabase - Full Backup."""
    check_staff(user_data)

    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    client = supabase_manager.get_client()
    if not client:
        return {"success": False, "message": "Supabase no está configurado"}

    logger.info("ADMIN: Starting FULL BACKUP to Supabase...")

    res_users = await handle_admin_sync_users_cloud({}, user_data)
    res_library = await handle_admin_sync_library_cloud({}, user_data)

    if res_users.get("success") and res_library.get("success"):
        return {
            "success": True,
            "message": "Respaldo completo realizado con éxito en Supabase.",
            "details": {
                "users": res_users.get("stats"),
                "library": res_library.get("stats"),
            },
        }
    else:
        return {
            "success": False,
            "message": "El respaldo se realizó parcialmente con errores.",
            "errors": {
                "users": res_users.get("message") if not res_users.get("success") else "OK",
                "library": res_library.get("message") if not res_library.get("success") else "OK",
            },
        }


async def handle_admin_sync_users_cloud(data: dict[str, Any], user_data: dict[str, Any]):
    """Sincroniza usuarios y niveles locales (Postgres) a Supabase."""
    check_staff(user_data)

    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    try:
        from models.user_models import User, UserLevel

        client = supabase_manager.get_client()

        async with pg_manager.get_session() as session:
            # 1. Sync User Levels
            res_levels = await session.execute(select(UserLevel))
            levels = res_levels.scalars().all()

            for lvl in levels:
                lvl_data = {
                    "id": lvl.id,
                    "name": lvl.name,
                    "priority": lvl.priority,
                    "color": lvl.color,
                    "ui_theme": lvl.ui_theme,
                    "ui_primary_color": lvl.ui_primary_color,
                    "ui_font_size": lvl.ui_font_size,
                    "ui_nav_opacity": lvl.ui_nav_opacity,
                    "ui_glass_blur": lvl.ui_glass_blur,
                    "ui_cover_width": lvl.ui_cover_width,
                    "ui_accent_opacity": lvl.ui_accent_opacity,
                    "panel_transparency": lvl.panel_transparency,
                    "background_color": lvl.background_color,
                    "card_color": lvl.card_color,
                    "banner_content_offset": lvl.banner_content_offset,
                    "force_settings": lvl.force_settings,
                    "price": lvl.price,
                    "can_download": lvl.can_download,
                    "can_read": lvl.can_read,
                    "daily_downloads": lvl.daily_downloads,
                    "has_mini_app_access": lvl.has_mini_app_access,
                    "has_library_access": lvl.has_library_access,
                    "can_request_books": lvl.can_request_books,
                    "can_upload_epub": lvl.can_upload_epub,
                    "early_access": lvl.early_access,
                    "custom_themes": lvl.custom_themes,
                    "allow_theme_templates": lvl.allow_theme_templates,
                    "show_recommendations": lvl.show_recommendations,
                    "default_theme_id": lvl.default_theme_id,
                }
                try:
                    client.table("user_levels").upsert(lvl_data).execute()
                except Exception as upsert_e:
                    logger.warning(f"Supabase upsert error for user_level {lvl.id}: {upsert_e}")

            # 2. Sync Users
            res_users = await session.execute(select(User))
            users = res_users.scalars().all()

            user_batch = []
            for u in users:
                u_data = {
                    "telegram_id": u.telegram_id,
                    "username": u.username,
                    "name": u.name,
                    "nickname": u.nickname,
                    "photo_url": u.photo_url,
                    "level_id": u.level_id,
                    "role": u.role,
                    "beta_tester": u.beta_tester,
                    "has_library_access": u.has_library_access,
                    "can_request_books": u.can_request_books,
                    "can_upload_epub": u.can_upload_epub,
                    "total_downloads": u.total_downloads,
                    "insignias": u.insignias,
                    "settings": u.settings,
                    "expires_at": u.expires_at.isoformat() if u.expires_at else None,
                }
                user_batch.append(u_data)

            if user_batch:
                for i in range(0, len(user_batch), 50):
                    batch = user_batch[i : i + 50]
                    try:
                        client.table("users").upsert(batch).execute()
                    except Exception as upsert_e:
                        logger.error(
                            f"Supabase PUSH error for user batch (indices {i}-{i + len(batch) - 1}): {upsert_e}"
                        )

            # 3. Pull from Supabase to ensure Local is up to date (Bidirectional)
            logger.info(
                "ADMIN: Triggering immediate PULL from Supabase to Local to sync missing data"
            )
            from core.optimized_sync_engine import optimized_sync_engine

            await optimized_sync_engine.force_sync_all()
            try:
                await optimized_sync_engine._sync_users_optimized()
                await optimized_sync_engine._sync_user_levels_optimized()
                await optimized_sync_engine._sync_admins_optimized()
            except Exception as pull_e:
                logger.error(f"Error during bidirectional PULL: {pull_e}")
                return {
                    "success": True,
                    "message": f"Push completado ({len(users)} users), pero el Pull falló: {pull_e}",
                }

            return {
                "success": True,
                "message": f"Sincronización bidireccional completada. Pushed {len(users)} users, Local updated from Cloud.",
                "stats": {"users_pushed": len(users), "levels_pushed": len(levels)},
            }
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_admin_sync_library_cloud(data: dict[str, Any], user_data: dict[str, Any]):
    """Sincroniza metadatos de series, propuestas IA, feedback, fuentes y libros locales con Supabase."""
    check_staff(user_data)
    return await SyncService.sync_library_to_cloud()


async def handle_admin_scan_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates forced library scan."""
    check_staff(user_data)
    force = data.get("force", False)
    soft = data.get("soft", False)

    def run_scan_in_thread(scanner_obj, force_val, soft_val):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info(f"Background scan thread started (Force: {force_val}, Soft: {soft_val})")
            loop.run_until_complete(scanner_obj.sync_all(force_scan=force_val, soft_scan=soft_val))
            logger.info("Background scan thread completed successfully.")
        except Exception as e:
            logger.error(f"Background scan thread error: {e}")
        finally:
            loop.close()

    try:
        if ScannerService._is_scanning:
            return {
                "success": False,
                "message": "⚠️ Ya hay un escaneo de librería en progreso.",
            }

        libs_json = os.getenv("LOCAL_LIBRARIES")
        if not libs_json:
            return {"success": False, "message": "LOCAL_LIBRARIES no configurada."}

        scanner = ScannerService(libs_json)
        t = threading.Thread(target=run_scan_in_thread, args=(scanner, force, soft))
        t.start()

        return {
            "success": True,
            "message": "Escaneo iniciado en segundo plano (Thread).",
        }
    except Exception as e:
        logger.error(f"Error starting background scan: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_cleanup_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Checks for physical existence of all books and cleans up the database."""
    check_staff(user_data)
    from utils.library_db import get_session

    try:
        with get_session() as session:
            stats = ScannerService.cleanup_library_orphans(
                session, user_id=user_data.get("user_id")
            )
            return {
                "success": True,
                "message": f"Limpieza completada: Se eliminaron {stats['deleted_books']} libros y {stats['deleted_series']} series inexistentes.",
                "stats": stats,
            }
    except Exception as e:
        logger.error(f"Error during library cleanup: {e}")
        return {"success": False, "message": f"Error during cleanup: {str(e)}"}


async def handle_admin_scan_series(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates forced scan for a specific series."""
    check_staff(user_data)
    series_hash = data.get("series_hash")
    force = data.get("force", True)

    if not series_hash:
        return {"success": False, "message": "series_hash es requerido."}

    def run_series_scan_in_thread(scanner_obj, s_hash, force_val):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info(
                f"Background series scan thread started (Hash: {s_hash}, Force: {force_val})"
            )
            loop.run_until_complete(scanner_obj.sync_series(s_hash, force_scan=force_val))
            logger.info(f"Background series scan thread for {s_hash} completed successfully.")
        except Exception as e:
            logger.error(f"Background series scan thread error for {s_hash}: {e}")
        finally:
            loop.close()

    try:
        if ScannerService._is_scanning:
            return {
                "success": False,
                "message": "⚠️ Ya hay un escaneo de librería en progreso.",
            }

        libs_json = os.getenv("LOCAL_LIBRARIES")
        scanner = ScannerService(libs_json or "{}")
        t = threading.Thread(target=run_series_scan_in_thread, args=(scanner, series_hash, force))
        t.start()
        return {"success": True, "message": "Sincronización de serie iniciada en segundo plano."}
    except Exception as e:
        logger.error(f"Error starting background series scan: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_scan_status(data: dict[str, Any], user_data: dict[str, Any]):
    """Returns current library scan progress."""
    check_staff(user_data)
    return {
        "success": True,
        "is_scanning": ScannerService._is_scanning,
        "progress": ScannerService._current_progress,
    }


async def handle_admin_reset_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Reset complete library database (admin only, requires confirmation)."""
    check_staff(user_data)
    if not data.get("confirmed", False):
        return {
            "success": False,
            "message": "Confirmación requerida para eliminar la base de datos.",
            "requireConfirmation": True,
        }

    try:
        import sqlalchemy as sa

        from utils.library_db import COVERS_DIR, engine, init_library_db

        items_deleted = []
        cover_count = 0

        try:
            with engine.begin() as conn:
                conn.execute(sa.text("DELETE FROM user_ratings"))
                conn.execute(sa.text("DELETE FROM user_downloads"))
                conn.execute(sa.text("DELETE FROM metadata_proposals"))
                conn.execute(sa.text("DELETE FROM ai_learning_feedback"))
                conn.execute(sa.text("DELETE FROM local_books"))
                conn.execute(sa.text("DELETE FROM series_metadata"))
                conn.execute(sa.text("DELETE FROM library_sources"))
                conn.execute(sa.text("DELETE FROM duplicate_books"))
                conn.execute(sa.text("DELETE FROM upload_books"))
            items_deleted.append("Tablas de PostgreSQL limpiadas")
        except Exception as e:
            logger.error(f"Error clearing Postgres tables: {e}")
            return {"success": False, "message": f"Error limpiando tablas Postgres: {e}"}

        if os.path.exists(COVERS_DIR):
            try:
                cover_count = len(
                    [
                        f
                        for f in os.listdir(COVERS_DIR)
                        if os.path.isfile(os.path.join(COVERS_DIR, f))
                    ]
                )
                shutil.rmtree(COVERS_DIR)
                items_deleted.append(f"{cover_count} portadas eliminadas")
            except Exception as e:
                logger.error(f"Error deleting covers: {e}")

        try:
            os.makedirs(COVERS_DIR, exist_ok=True)
            items_deleted.append("Directorio de portadas recreado")
        except Exception as e:
            logger.error(f"Error recreating covers dir: {e}")

        try:
            init_library_db()
            items_deleted.append("Base de datos recreada con esquema correcto")
        except Exception as e:
            logger.error(f"Error recreating database schema: {e}")

        logger.info(f"Admin {user_data.get('telegram_id')} reset library database.")
        return {
            "success": True,
            "message": "Base de datos local reseteada exitosamente.",
            "details": items_deleted,
            "coversDeleted": cover_count,
        }
    except Exception as e:
        logger.error(f"Error en handle_admin_reset_library: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_restart_docker(data: dict[str, Any], user_data: dict[str, Any]):
    """Restart Docker container (admin only)."""
    check_staff(user_data)
    import subprocess

    try:
        container_name = os.getenv("CONTAINER_NAME", "zeepub-bot")

        async def do_restart():
            try:
                await asyncio.to_thread(
                    subprocess.run, ["docker", "restart", container_name], timeout=30
                )
            except Exception as e:
                logger.error(f"Error in background docker restart: {e}")

        asyncio.create_task(do_restart())
        return {
            "success": True,
            "message": f"Contenedor {container_name} reiniciándose...",
            "restarting": True,
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_admin_update_system(data: dict[str, Any], user_data: dict[str, Any]):
    """Trigger system update (git pull + restart) using existing bot infrastructure."""
    check_staff(user_data)
    try:
        from services.maintenance_service import trigger_watchtower_update

        asyncio.create_task(trigger_watchtower_update())
        return {
            "success": True,
            "message": "Actualización solicitada. El bot contactará con Watchtower para buscar nuevas versiones y se reiniciará si es necesario.",
            "restarting": True,
        }
    except Exception as e:
        logger.error(f"Error en handle_admin_update_system: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_tier_config(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene la configuración completa de un nivel/tier."""
    check_staff(user_data)
    tier_name = data.get("name")
    tier_id = data.get("id")

    # Check Global
    is_global = False
    if tier_id and str(tier_id).lower() == "global":
        is_global = True
    elif tier_name and "global" in str(tier_name).lower():
        is_global = True

    if is_global:
        global_raw = get_setting("ui_defaults_global", "{}")
        g = json.loads(global_raw)
        global_config = {
            "id": "global",
            "name": "Global",
            "icon": "globe",
            "color": "#ffffff",
            "dailyDownloads": -1,
            "maxConcurrent": 10,
            "priorityRequests": True,
            "earlyAccess": True,
            "customThemes": True,
            "primaryColor": g.get("primaryColor", "#2b6cee"),
            "glassOpacity": g.get("glassOpacity", 0.6),
            "theme": g.get("theme", "dark"),
            "fontSize": g.get("fontSize", 14),
            "glassBlur": g.get("glassBlur", 12),
            "coverWidth": g.get("coverWidth", 120),
            "navOpacity": g.get("navOpacity", 0.8),
            "accentOpacity": g.get("accentOpacity", 0.2),
            "showRecommendations": g.get("showRecommendations", True),
            "canDownload": g.get("canDownload", True),
            "canRead": g.get("canRead", True),
            "canUploadEpub": g.get("canUploadEpub", False),
            "forceSettings": g.get("forceSettings", False),
            "cardGlowIntensity": g.get("cardGlowIntensity", 0.5),
            "backgroundColor": g.get("backgroundColor", "#0f172a"),
            "cardColor": g.get("cardColor", "#1e293b"),
            "bannerContentOffset": g.get("bannerContentOffset", 0),
            "allowThemeTemplates": g.get("allowThemeTemplates", False),
        }
        return {"success": True, "config": global_config, "tier": global_config}

    tier = None
    if tier_id:
        tier = await user_repo.get_level_by_id(int(tier_id))
    elif tier_name and str(tier_name).isdigit():
        tier = await user_repo.get_level_by_id(int(tier_name))
    elif tier_name:
        all_lvls = await user_repo.get_all_levels()
        tier = next(
            (lvl for lvl in all_lvls if lvl["name"].lower() == tier_name.lower()),
            None,
        )

    if not tier:
        raise HTTPException(status_code=404, detail="Tier not found")

    return {"success": True, "config": tier, "tier": tier}


async def handle_admin_save_tier_config(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda la configuración completa de un nivel/tier."""
    check_staff(user_data)
    tier_name = data.get("name")
    level_id = data.get("level_id") or data.get("id")

    is_global = (
        level_id == "global" or tier_name == "Global" or (tier_name and "Global" in str(tier_name))
    )

    if is_global:
        ui_settings = {}
        field_mapping = {
            "primaryColor": "primaryColor",
            "glassOpacity": "glassOpacity",
            "navOpacity": "navOpacity",
            "glassBlur": "glassBlur",
            "coverWidth": "coverWidth",
            "showRecommendations": "showRecommendations",
            "theme": "theme",
            "fontSize": "fontSize",
            "accentOpacity": "accentOpacity",
            "canDownload": "canDownload",
            "canRead": "canRead",
            "hasLibraryAccess": "hasLibraryAccess",
            "canRequestBooks": "canRequestBooks",
            "bannerContentOffset": "bannerContentOffset",
            "backgroundColor": "backgroundColor",
            "cardColor": "cardColor",
            "forceSettings": "forceSettings",
            "cardGlowIntensity": "cardGlowIntensity",
            "allowThemeTemplates": "allowThemeTemplates",
        }

        for frontend_key, setting_key in field_mapping.items():
            if frontend_key in data:
                val = data[frontend_key]
                if (
                    frontend_key == "glassOpacity"
                    or frontend_key == "navOpacity"
                    or frontend_key == "accentOpacity"
                ):
                    if isinstance(val, int | float) and val > 1:
                        val = val / 100.0
                ui_settings[setting_key] = val

        if "name" in data:
            ui_settings["name"] = data["name"]

        current_global = json.loads(get_setting("ui_defaults_global", "{}"))
        current_global.update(ui_settings)
        set_setting("ui_defaults_global", json.dumps(current_global))
        return {"success": True, "tierId": "global"}

    # Not global
    client = supabase_manager.get_client()
    tier_id = None
    if level_id and str(level_id).isdigit():
        tier_id = int(level_id)
    else:
        # Find ID by name
        result = client.table("user_levels").select("id").ilike("name", tier_name).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Tier '{tier_name}' no encontrado")
        tier_id = result.data[0]["id"]

    update_data = {}
    field_mapping = {
        "name": "name",
        "icon": "icon",
        "color": "color",
        "dailyDownloads": "daily_downloads",
        "maxConcurrent": "max_concurrent",
        "priorityRequests": "priority_requests",
        "earlyAccess": "early_access",
        "customThemes": "custom_themes",
        "primaryColor": "ui_primary_color",
        "glassOpacity": "panel_transparency",
        "theme": "ui_theme",
        "fontSize": "ui_font_size",
        "glassBlur": "ui_glass_blur",
        "coverWidth": "ui_cover_width",
        "navOpacity": "ui_nav_opacity",
        "accentOpacity": "ui_accent_opacity",
        "showRecommendations": "show_recommendations",
        "canDownload": "can_download",
        "canRead": "can_read",
        "canUploadEpub": "can_upload_epub",
        "hasLibraryAccess": "has_library_access",
        "canRequestBooks": "can_request_books",
        "bannerContentOffset": "banner_content_offset",
        "backgroundColor": "background_color",
        "cardColor": "card_color",
        "forceSettings": "force_settings",
        "cardGlowIntensity": "ui_glow_intensity",
        "ui_exported_settings": "ui_exported_settings",
        "allowThemeTemplates": "allow_theme_templates",
        "defaultThemeId": "default_theme_id",
    }

    for frontend_key, db_key in field_mapping.items():
        if frontend_key in data and data[frontend_key] is not None:
            val = data[frontend_key]
            if db_key == "panel_transparency":
                try:
                    val = int(float(val) * 100)
                except (ValueError, TypeError):
                    val = 70
            update_data[db_key] = val

    try:
        client.table("user_levels").update(update_data).eq("id", tier_id).execute()
    except Exception as e:
        logger.warning(f"Supabase update error: {e}. Attempting local only update.")

    await user_repo.update_level(tier_id, data)

    from core.optimized_sync_engine import optimized_sync_engine

    await optimized_sync_engine.force_sync_all()

    return {"success": True, "tierId": tier_id}


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
            suffixes = ["(Nuevo)", "(Alt)", "(Pro)", "(Custom)", "(Modern)", "(Premium)"]
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
        from dateutil import parser

        from repositories.user_repository import user_repo
        from services.user_audit_service import UserAuditService
        from services.user_service import invalidate_user_cache

        existing = await user_repo.get_by_id(int(user_id), as_dict=True)
        if not existing:
            await user_repo.create_minimal_user(int(user_id))
            existing = await user_repo.get_by_id(int(user_id), as_dict=True)

        expires_at = None
        if data.get("expiresAt"):
            try:
                expires_at = parser.parse(data["expiresAt"])
            except Exception:
                pass

        # Determine level_id and role
        role = data.get("role", existing.get("role", "free"))

        level_id = data.get("levelId")
        if not level_id:
            # Fallback for old frontend versions
            level_to_id = {"admin": 1, "staff": 2, "premium": 3, "vip": 4, "white": 5}
            level_id = level_to_id.get(str(data.get("level", "")).lower(), 6)
        else:
            level_id = int(level_id)  # Ensure it's an integer if provided

        # Enforcement: bypassLimits only for Premium+ (ID <= 3)
        if data.get("bypassLimits") and level_id > 3:
            logger.warning(f"Blocking bypassLimits for user {user_id} - level too low ({level_id})")
            data["bypassLimits"] = False

        if data.get("isAdmin"):
            role = "admin"
            level_id = 1

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
            "bypassLimits": "bypass_limits",
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
            bypass_limits=data.get("bypassLimits"),
            can_request_books=data.get("canRequestBooks"),
            can_upload_epub=data.get("canUploadEpub"),
            level_id=level_id,
            settings=data.get("settings"),
            allow_theme_templates=data.get("allowThemeTemplates"),
            beta_tester=data.get("betaTester"),
            sync_to_supabase=True,
        )

        # beta_tester is now handled in upsert

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
        raw_user = await user_repo.get_by_id(int(user_id), as_dict=True)

        if not access_info or not raw_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "success": True,
            "user": {
                "id": str(user_id),
                "username": raw_user.get("username") or f"User_{user_id}",
                "name": raw_user.get("nickname") or raw_user.get("name") or f"User_{user_id}",
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
                "bypassLimits": raw_user.get("bypass_limits", False),
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
    from models.library_models import LocalBook
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
    import os

    from models.library_models import DownloadHistory, LocalBook, UserDownload, UserRating
    from utils.library_db import get_session

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
                session.query(DownloadHistory).filter(DownloadHistory.book_id == book.id).update(
                    {DownloadHistory.book_id: None}, synchronize_session=False
                )
                session.query(UserDownload).filter(UserDownload.book_id == book.id).update(
                    {UserDownload.book_id: None}, synchronize_session=False
                )
                session.query(UserRating).filter(UserRating.book_id == book.id).update(
                    {UserRating.book_id: None}, synchronize_session=False
                )

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
    import os

    from models.library_models import (
        ArchivedBook,
        LocalBook,
    )
    from utils.library_db import get_session

    dup_id = data.get("id")
    target = data.get("target")

    session = get_session()
    try:
        dup_record = session.query(DuplicateBook).filter_by(id=dup_id).first()
        if not dup_record:
            return {"success": False, "message": "Registro no encontrado"}

        path_to_delete = (
            dup_record.original_filepath if target == "original" else dup_record.duplicate_filepath
        )

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

    from sqlalchemy import desc

    from utils.library_db import get_session

    session = get_session()
    try:
        dups = session.query(DuplicateBook).order_by(desc(DuplicateBook.detected_at)).all()
        result = [
            {
                "id": d.id,
                "title": d.title,
                "author": d.author,
                "hash": d.book_hash,
                "original": d.original_filepath,
                "duplicate": d.duplicate_filepath,
                "detectedAt": d.detected_at.isoformat() if d.detected_at else None,
            }
            for d in dups
        ]
        return {"success": True, "duplicates": result}
    finally:
        session.close()


async def handle_admin_recheck_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")

    # Placeholder for complex re-check logic to save space, but functional
    import os

    from utils.library_db import get_session

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
    from utils.library_db import get_session

    session = get_session()
    session.query(DuplicateBook).delete()
    session.commit()
    session.close()
    return {"success": True}


async def handle_admin_ai_series_duplicate_scan(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    import asyncio
    import threading

    from services.library_service import LibraryService

    def run_ai_scan_in_thread():
        # Crear un nuevo loop para el hilo secundario
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            LibraryService._is_ai_scanning = True
            logger.info("🤖 Iniciando escaneo de duplicados por IA en segundo plano...")
            loop.run_until_complete(LibraryService.find_ai_series_duplicates())
            logger.info("🏁 Escaneo de duplicados por IA finalizado con éxito.")
        except Exception as e:
            logger.error(
                f"❌ Error en escaneo de duplicados por IA (Background): {e}", exc_info=True
            )
        finally:
            LibraryService._is_ai_scanning = False
            loop.close()

    try:
        if LibraryService._is_ai_scanning:
            return {
                "success": False,
                "message": "⚠️ Ya hay un escaneo de duplicados por IA en curso.",
            }

        t = threading.Thread(target=run_ai_scan_in_thread)
        t.start()

        return {
            "success": True,
            "message": "Escaneo de duplicados por IA iniciado en segundo plano. Las propuestas aparecerán en la lista progresivamente.",
        }
    except Exception as e:
        logger.error(f"Error starting background AI scan: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_ai_scan_status(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    from services.library_service import LibraryService

    return {
        "success": True,
        "is_scanning": LibraryService._is_ai_scanning,
    }


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

    logs = log_buffer_handler.get_logs(
        level=data.get("level", "INFO"), last_hours=data.get("hours")
    )
    return {"success": True, "logs": logs}


async def handle_admin_send_logs_telegram(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    try:
        import io
        from datetime import datetime

        from api.main import bot as bot_instance
        from utils.log_manager import log_buffer_handler

        level = data.get("level", "DEBUG")
        hours = data.get("hours")

        logs = log_buffer_handler.get_logs(level=level, last_hours=hours)
        if not logs:
            return {"success": False, "message": "No hay logs disponibles para enviar."}

        # Format logs
        log_text = "\n".join(
            [
                f"[{log_entry['time']}] {log_entry['level']}: {log_entry['msg']}"
                for log_entry in logs
            ]
        )

        # Create file
        file_obj = io.BytesIO(log_text.encode("utf-8"))

        # Filename with range
        if logs:
            first_t = logs[0]["timestamp"]
            last_t = logs[-1]["timestamp"]
        else:
            first_t = last_t = datetime.now().timestamp()

        def fmt(t):
            return datetime.fromtimestamp(t).strftime("%Y%m%d_%H%M")

        filename = f"logs_{fmt(first_t)}_{fmt(last_t)}.txt"
        file_obj.name = filename

        user_id = user_data.get("user_id")

        # Send via Telegram
        await bot_instance.app.bot.send_document(
            chat_id=user_id,
            document=file_obj,
            caption=f"📄 <b>Logs del Sistema</b>\nFiltro: {level}\nPeriodo: {fmt(first_t)} a {fmt(last_t)}",
            parse_mode="HTML",
        )

        return {
            "success": True,
            "message": "Logs enviados a tu Telegram correctamente.",
        }
    except Exception as e:
        logger.error(f"Error sending logs to Telegram: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}


async def handle_admin_bulk_upload_confirm(data: dict[str, Any], user_data: dict[str, Any]):
    """Confirma y finaliza múltiples subidas de EPUB."""
    selected_ids = data.get("selected_ids", [])
    discarded_ids = data.get("discarded_ids", [])

    # Si no vienen selected_ids, probamos con upload_ids (compatibilidad)
    if not selected_ids:
        selected_ids = data.get("upload_ids", [])

    if not selected_ids and not discarded_ids:
        raise HTTPException(status_code=400, detail="No selected or discarded IDs provided")

    from pathlib import Path

    from handlers.epub_upload_handler import epub_uploader, pending_uploads

    # 1. Manejar descartados (limpieza)
    for disc_id in discarded_ids:
        if disc_id in pending_uploads:
            info = pending_uploads[disc_id]
            epub_uploader.cleanup_upload(disc_id, Path(info["file_path"]))

    # 2. Manejar seleccionados (procesamiento)
    results = []
    for upload_id in selected_ids:
        if upload_id not in pending_uploads:
            results.append({"upload_id": upload_id, "success": False, "error": "No encontrado"})
            continue

        upload_info = pending_uploads[upload_id]
        file_path = Path(upload_info["file_path"])
        metadata = upload_info["metadata"]
        suggested_path = metadata.get("suggested_path")

        try:
            success = await epub_uploader.add_to_library(file_path, suggested_path, metadata)
            if success:
                epub_uploader._log_history(
                    user_id=upload_info["user_id"],
                    filename=upload_info["original_filename"],
                    book_hash=metadata.get("book_hash"),
                    status="success",
                    final_path=suggested_path,
                )
                epub_uploader.cleanup_upload(upload_id, file_path)
                results.append({"upload_id": upload_id, "success": True})
            else:
                epub_uploader._log_history(
                    user_id=upload_info["user_id"],
                    filename=upload_info["original_filename"],
                    book_hash=metadata.get("book_hash"),
                    status="error",
                    error_message="Failed to move file to library",
                )
                results.append(
                    {
                        "upload_id": upload_id,
                        "success": False,
                        "error": "Error al mover a librería",
                    }
                )
        except Exception as e:
            results.append({"upload_id": upload_id, "success": False, "error": str(e)})

    return {"success": True, "results": results}


async def handle_get_upload_history(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene el historial de subidas paginado."""
    check_staff(user_data)
    limit = data.get("limit", 100)
    offset = data.get("offset", 0)

    try:
        async with pg_manager.get_session() as session:
            stmt = (
                select(UploadHistory)
                .order_by(desc(UploadHistory.created_at))
                .limit(limit)
                .offset(offset)
            )
            results = (await session.execute(stmt)).scalars().all()

            history_list = []
            for item in results:
                history_list.append(
                    {
                        "id": item.id,
                        "user_id": item.user_id,
                        "filename": item.filename,
                        "book_hash": item.book_hash,
                        "status": item.status,
                        "final_path": item.final_path,
                        "error_message": item.error_message,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                    }
                )
            return {"history": history_list}
    except Exception as e:
        logger.error(f"Error fetching upload history: {e}")
        return {"history": []}


async def handle_admin_enrich_metadata(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates manual enrichment of metadata from online sources."""
    check_staff(user_data)

    def run_enrichment_in_thread(scanner_obj):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info("Background metadata enrichment thread started")
            scanner_obj.enrich_all_metadata()
            logger.info("Background metadata enrichment thread completed.")
        except Exception as e:
            logger.error(f"Background enrichment thread error: {e}")
        finally:
            loop.close()

    try:
        from services.scanner_service import ScannerService

        libs_json = os.getenv("LOCAL_LIBRARIES")
        scanner = ScannerService(libs_json or "{}")

        t = threading.Thread(target=run_enrichment_in_thread, args=(scanner,))
        t.start()

        return {
            "success": True,
            "message": "Enriquecimiento de metadatos iniciado en segundo plano. Se procesarán libros con ISBN que no tengan título en español o descripción.",
        }
    except Exception as e:
        logger.error(f"Error starting enrichment task: {e}")
        return {"success": False, "message": str(e)}
