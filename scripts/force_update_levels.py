import asyncio
import logging
from sqlalchemy import text
from core.db_manager_pg import pg_manager
from repositories.user_repository import user_repo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_update_levels():
    """
    Actualiza los niveles de usuario en la base de datos con los valores definidos 
    en el método get_default_levels() de UserRepository.
    """
    logger.info("Iniciando actualización forzada de niveles de usuario...")
    
    # Obtener los niveles definidos en el código
    default_levels = user_repo.get_default_levels()
    
    async with pg_manager.get_session() as session:
        for level in default_levels:
            l_id = int(level["id"])
            name = level["name"]
            
            logger.info(f"Actualizando nivel: {name} (ID: {l_id})")
            
            # Upsert (Insert or Update)
            await session.execute(text("""
                INSERT INTO user_levels (
                    id, name, priority, color, price, daily_downloads, 
                    can_download, can_read, has_mini_app_access, 
                    has_library_access, can_request_books, can_upload_epub, 
                    early_access, custom_themes, allow_theme_templates, show_recommendations
                ) VALUES (
                    :id, :name, :priority, :color, :price, :daily_downloads, 
                    :can_download, :can_read, :has_mini_app_access, 
                    :has_library_access, :can_request_books, :can_upload_epub, 
                    :early_access, :custom_themes, :allow_theme_templates, :show_recommendations
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    priority = EXCLUDED.priority,
                    color = EXCLUDED.color,
                    daily_downloads = EXCLUDED.daily_downloads,
                    can_download = EXCLUDED.can_download,
                    can_read = EXCLUDED.can_read,
                    has_mini_app_access = EXCLUDED.has_mini_app_access,
                    has_library_access = EXCLUDED.has_library_access,
                    can_request_books = EXCLUDED.can_request_books,
                    can_upload_epub = EXCLUDED.can_upload_epub,
                    early_access = EXCLUDED.early_access,
                    custom_themes = EXCLUDED.custom_themes,
                    allow_theme_templates = EXCLUDED.allow_theme_templates,
                    show_recommendations = EXCLUDED.show_recommendations
            """), {
                "id": l_id,
                "name": name,
                "priority": level["priority"],
                "color": level["color"],
                "price": level["price"],
                "daily_downloads": level["dailyDownloads"],
                "can_download": level["canDownload"],
                "can_read": level["canRead"],
                "has_mini_app_access": level["hasAccess"],
                "has_library_access": level.get("has_library_access", True),
                "can_request_books": level.get("can_request_books", True),
                "can_upload_epub": level.get("canUploadEpub", False),
                "early_access": level["earlyAccess"],
                "custom_themes": level["customThemes"],
                "allow_theme_templates": level["allowThemeTemplates"],
                "show_recommendations": level.get("show_recommendations", True)
            })
        
        await session.commit()
        logger.info("✅ Todos los niveles han sido actualizados con los nuevos valores de descarga.")

if __name__ == "__main__":
    asyncio.run(force_update_levels())
