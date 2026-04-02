
import asyncio
import logging
from utils.metadata_utils import parse_metadata_from_title, generar_slug_from_meta, get_series_spanish_from_api

# Configurar logging para ver los mensajes de los helpers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_metadata_parsing():
    print("\n--- Test: parse_metadata_from_title ---")
    titles = [
        "Re:Zero - Starting Life in Another World, Vol. 1",
        "No Game No Life, Vol. 1",
        "Mushoku Tensei: Jobless Reincarnation Vol. 1",
        "That Time I Got Reincarnated as a Slime, Vol. 01 (Light Novel)",
    ]
    
    for t in titles:
        res = parse_metadata_from_title(t)
        print(f"Original: {t}")
        print(f"  Series: {res['series']}")
        print(f"  Volume: {res['volume']}")
        print("-" * 20)

async def test_slug_generation():
    print("\n--- Test: generar_slug_from_meta (Priority English) ---")
    meta = {
        "series_name": "Re:Zero kara Hajimeru Isekai Seikatsu",
        "series_english": "Re:Zero - Starting Life in Another World",
    }
    slug = generar_slug_from_meta(meta)
    print(f"Meta: {meta}")
    print(f"Generated Slug: {slug}")
    
    meta_no_eng = {
        "series_name": "Mushoku Tensei",
        "series_english": None
    }
    slug_no_eng = generar_slug_from_meta(meta_no_eng)
    print(f"Meta (No English): {meta_no_eng}")
    print(f"Generated Slug: {slug_no_eng}")

async def test_spanish_enrichment():
    print("\n--- Test: get_series_spanish_from_api (Google Books) ---")
    # Nota: Esto requiere conexión a internet y que el entorno lo permita.
    test_cases = [
        ("Overlord", "Kugane Maruyama"),
        ("Re:Zero", "Tappei Nagatsuki"),
        ("Boushoku no Berserk", None)
    ]
    
    for name, author in test_cases:
        print(f"Buscando: {name} (Autor: {author})")
        spanish = await get_series_spanish_from_api(name, author)
        print(f"  Resultado: {spanish}")
        print("-" * 20)

async def main():
    await test_metadata_parsing()
    await test_slug_generation()
    # Descomentar si quieres probar la API real (puede fallar por red/timeout en el entorno)
    await test_spanish_enrichment()

if __name__ == "__main__":
    asyncio.run(main())
