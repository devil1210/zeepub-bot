"""
Script para actualizar el template de publicación por defecto.
Uso: python execution/update_template.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text


TEMPLATE_CONTENT = """{serie} ║ {series_spanish} ║ {titulo}
[?volumen]Volumen {volumen}[/?]
#{slug}

Maquetado por: #ZeePub
Categoría: {tipo}
[?demography]Demografía: {demography}[/?]
[?genres]Géneros: {genres}[/?]
[?autor]Autor: {autor}[/?]
[?illustrator]Ilustrador: {illustrator}[/?]
[?published_at]Publicado: {published_at}[/?]
[?traductor]Traducción: {traductor}[/?]
---
<b>Sinopsis:</b>

{sinopsis}

#{slug}
---
📂 {titulo}
ℹ️ Versión Epub: {version}
📅 Actualizado: {fecha}
📦 Tamaño: {tamaño}
[?rating]⭐️ {rating}[/?]
#{slug}"""


async def main():
    from core.db_manager_pg import pg_manager

    print("Actualizando template de publicación...")

    async with pg_manager.get_session() as session:
        result = await session.execute(
            text("SELECT id FROM publication_templates WHERE name = :name"), {"name": "Estándar Telegram"}
        )
        existing = result.fetchone()

        if existing:
            await session.execute(
                text("""
                    UPDATE publication_templates 
                    SET content = :content 
                    WHERE id = :id
                """),
                {"content": TEMPLATE_CONTENT, "id": existing[0]},
            )
            print(f"Template actualizado (ID: {existing[0]})")
        else:
            result = await session.execute(
                text("""
                    INSERT INTO publication_templates (name, content, platform)
                    VALUES (:name, :content, :platform)
                    RETURNING id
                """),
                {"name": "Estándar Telegram", "content": TEMPLATE_CONTENT, "platform": "telegram"},
            )
            new_id = result.fetchone()[0]
            print(f"Template creado (ID: {new_id})")

        await session.commit()

    print("Listo!")


if __name__ == "__main__":
    asyncio.run(main())
