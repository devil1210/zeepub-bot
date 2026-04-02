import asyncio
import re
from sqlalchemy import text
from core.db_manager_pg import pg_manager

def old_extract_romaji(title: str) -> str:
    if not title:
        return ""
    latin_chars = re.sub(r"[^\w\s\-\:]", "", title)
    romaji = re.sub(r"\s+", " ", latin_chars).strip()
    return romaji if len(romaji) >= 3 else ""

def new_extract_romaji(title: str) -> str:
    if not title:
        return ""
    romaji = re.sub(r"\s+", " ", title).strip()
    return romaji if len(romaji) >= 3 else ""

async def fix_romaji():
    print("🔍 Buscando títulos afectados...")
    async with pg_manager.get_session() as session:
        res = await session.execute(text("SELECT id, title, series_spanish, series_english, romaji_title FROM local_books"))
        rows = res.fetchall()
        
        updates = 0
        
        for row in rows:
            book_id = row.id
            title = row.title
            series_spa = row.series_spanish
            series_eng = row.series_english
            current_romaji = row.romaji_title
            
            title_source = title or series_spa or series_eng or ""
            
            if current_romaji and current_romaji.strip():
                # Verificar si coincide exactamente con el resultado de la función agresiva anterior
                old_auto = old_extract_romaji(title_source)
                new_auto = new_extract_romaji(title_source)
                
                if current_romaji == old_auto and current_romaji != new_auto:
                    print(f"🔄 Corrigiendo ID {book_id}: '{current_romaji}' -> '{new_auto}'")
                    await session.execute(
                        text("UPDATE local_books SET romaji_title = :new_r WHERE id = :id"),
                        {"new_r": new_auto, "id": book_id}
                    )
                    updates += 1
        
        if updates > 0:
            await session.commit()
            print(f"\n✅ Operación completada. Se corrigieron {updates} libros afectados exitosamente.")
        else:
            print("\n✨ No se encontraron libros que necesiten corrección (o ya estaban bien).")

if __name__ == "__main__":
    asyncio.run(fix_romaji())
