"""
Script mejorado para renombrar temas duplicados con nombres únicos
Verifica qué temas existen realmente y renombra todos los que tienen "2"
"""

import asyncio
import logging
import sys

# Agregar el path del proyecto
sys.path.append('/app')

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config.config_settings import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_rename_themes():
    """Verifica temas existentes y renombra todos los que tienen '2' al final."""
    
    if not config.ENABLE_POSTGRES_PLUGIN:
        logger.error("PostgreSQL plugin not enabled")
        return
    
    DATABASE_URL = config.DATABASE_URL
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured")
        return
    
    logger.info("Starting enhanced theme renaming process...")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # 1. Obtener TODOS los temas existentes
            logger.info("Checking ALL existing themes...")
            result = await conn.execute(text("SELECT id, name FROM app_themes ORDER BY name"))
            all_themes = result.fetchall()
            
            logger.info(f"Found {len(all_themes)} total themes:")
            for theme in all_themes:
                logger.info(f"  - ID: {theme[0]}, Name: '{theme[1]}'")
            
            # 2. Encontrar temas que terminan con " 2" (espacio + número)
            themes_with_2 = []
            for theme in all_themes:
                name = theme[1]
                # Buscar nombres que terminan con espacio + número
                if name and ' 2' in name and name.strip().endswith('2'):
                    themes_with_2.append(theme)
                    logger.info(f"Found theme with '2': ID {theme[0]}, Name: '{name}'")
            
            if not themes_with_2:
                logger.info("No themes found ending with '2'. Checking for other patterns...")
                # Buscar otros patrones posibles
                for theme in all_themes:
                    name = theme[1]
                    if name and ('2' in name):
                        logger.info(f"Theme containing '2': ID {theme[0]}, Name: '{name}'")
                return
            
            logger.info(f"Found {len(themes_with_2)} themes to rename")
            
            # 3. Mapeo mejorado - genera nombres únicos automáticamente
            renamed_count = 0
            
            for theme_id, old_name in themes_with_2:
                # Extraer el nombre base (sin el " 2")
                base_name = old_name.replace(' 2', '').strip()
                
                # Generar nombres únicos basados en el patrón
                new_name_variants = [
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
                    f"{base_name} Blue",
                    f"{base_name} Green",
                    f"{base_name} Purple",
                    f"{base_name} Red",
                    f"{base_name} Orange",
                    f"{base_name} Yellow"
                ]
                
                # Intentar encontrar un nombre único
                new_name = None
                for candidate in new_name_variants:
                    # Verificar si el candidato ya existe
                    result = await conn.execute(text("SELECT id FROM app_themes WHERE name = :candidate"), {"candidate": candidate})
                    existing = result.fetchone()
                    
                    if not existing:
                        new_name = candidate
                        break
                
                if not new_name:
                    # Si todos los nombres están tomados, usar timestamp
                    import time
                    new_name = f"{base_name} ({int(time.time())})"
                    logger.warning(f"All name variants taken for '{old_name}', using timestamp: '{new_name}'")
                
                # Realizar el renombrado
                await conn.execute(
                    text("UPDATE app_themes SET name = :new_name, updated_at = CURRENT_TIMESTAMP WHERE id = :theme_id"),
                    {"new_name": new_name, "theme_id": theme_id}
                )
                
                logger.info(f"✅ Renamed theme ID {theme_id}: '{old_name}' → '{new_name}'")
                renamed_count += 1
            
            # 4. Verificación final
            logger.info(f"\nRenaming completed. {renamed_count} themes renamed.")
            
            logger.info("\nFinal theme list:")
            result = await conn.execute(text("SELECT id, name FROM app_themes ORDER BY name"))
            final_themes = result.fetchall()
            for theme in final_themes:
                logger.info(f"  - ID: {theme[0]}, Name: '{theme[1]}'")
                
        await engine.dispose()
        logger.info("Enhanced theme renaming process completed successfully")
        return {"status": "success", "renamed": renamed_count}
        
    except Exception as e:
        logger.error(f"Error in enhanced theme renaming: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(check_and_rename_themes())
