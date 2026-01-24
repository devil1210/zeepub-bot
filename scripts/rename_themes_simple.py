"""
Script para renombrar temas duplicados con nombres únicos
Se ejecuta como un comando del bot
"""

import asyncio
import logging

from sqlalchemy import text

from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapeo de temas con "2" al final a nuevos nombres únicos
THEME_RENAMES = {
    "Amoled Black 2": "Midnight Black",
    "Emerald Night 2": "Forest Green", 
    "Ocean Deep 2": "Deep Ocean",
    "Sunset Orange 2": "Golden Hour",
    "Purple Haze 2": "Lavender Dream",
    "Dark Blue 2": "Navy Blue",
    "Light Theme 2": "Pure White",
    "Rose Gold 2": "Pink Champagne",
    "Cyberpunk 2": "Neon Lights",
    "Minimal Dark 2": "Clean Slate"
}

async def rename_themes():
    """Renombrar temas duplicados con nombres únicos."""
    logger.info("Starting theme renaming process...")
    
    try:
        async with pg_manager.get_session() as session:
            # Verificar temas existentes
            logger.info("Checking existing themes...")
            result = await session.execute(text("SELECT id, name FROM app_themes ORDER BY name"))
            existing_themes = result.fetchall()
            
            logger.info(f"Found {len(existing_themes)} themes:")
            for theme in existing_themes:
                logger.info(f"  - ID: {theme[0]}, Name: {theme[1]}")
            
            # Renombrar temas
            renamed_count = 0
            for old_name, new_name in THEME_RENAMES.items():
                # Verificar si el tema con "2" existe
                result = await session.execute(text("SELECT id FROM app_themes WHERE name = :old_name"), {"old_name": old_name})
                theme_to_rename = result.fetchone()
                
                if theme_to_rename:
                    theme_id = theme_to_rename[0]
                    
                    # Verificar si el nuevo nombre ya existe
                    result = await session.execute(text("SELECT id FROM app_themes WHERE name = :new_name"), {"new_name": new_name})
                    existing_new = result.fetchone()
                    
                    if existing_new:
                        logger.warning(f"Cannot rename '{old_name}' to '{new_name}' - '{new_name}' already exists")
                        continue
                    
                    # Actualizar el nombre
                    await session.execute(
                        text("UPDATE app_themes SET name = :new_name, updated_at = CURRENT_TIMESTAMP WHERE id = :theme_id"),
                        {"new_name": new_name, "theme_id": theme_id}
                    )
                    
                    logger.info(f"✅ Renamed theme ID {theme_id}: '{old_name}' → '{new_name}'")
                    renamed_count += 1
                else:
                    logger.info(f"Theme '{old_name}' not found, skipping")
            
            await session.commit()
            
            # Mostrar resultado final
            logger.info(f"\nRenaming completed. {renamed_count} themes renamed.")
            
            # Verificar estado final
            logger.info("\nFinal theme list:")
            result = await session.execute(text("SELECT id, name FROM app_themes ORDER BY name"))
            final_themes = result.fetchall()
            for theme in final_themes:
                logger.info(f"  - ID: {theme[0]}, Name: {theme[1]}")
                
        logger.info("Theme renaming process completed successfully")
        return {"status": "success", "renamed": renamed_count}
        
    except Exception as e:
        logger.error(f"Error renaming themes: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(rename_themes())
