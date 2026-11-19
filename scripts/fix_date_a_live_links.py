import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import text
from core.db_manager_pg import pg_manager

DATE_A_LIVE_MAPPINGS = {
    # Vol 1
    "AKnpXdmNT4": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V01 [KPT].epub",
        "title": "Date A Live - Volumen 01",
        "vol": "1"
    },
    # Vol 2
    "sWwhLvA186": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V02 [KPT].epub",
        "title": "Date A Live - Volumen 02",
        "vol": "2"
    },
    # Vol 3 (ya funciona con OrgFf2DvHw, pero registramos por seguridad)
    "OrgFf2DvHw": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V03 [KPT].epub",
        "title": "Date A Live - Volumen 03",
        "vol": "3"
    },
    # Vol 4
    "wkmAKpNDdl": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V04 [KPT].epub",
        "title": "Date A Live - Volumen 04",
        "vol": "4"
    },
    # Vol 5
    "WQAaWtb3WD": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V05 [KPT].epub",
        "title": "Date A Live - Volumen 05",
        "vol": "5"
    },
    # Vol 6
    "xUCKODOjix": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V06 [KPT].epub",
        "title": "Date A Live - Volumen 06",
        "vol": "6"
    },
    # Vol 7
    "ESql3RU7ax": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V07 [KPT].epub",
        "title": "Date A Live - Volumen 07",
        "vol": "7"
    },
    # Vol 8
    "dSJidNwuA9": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V08 [KPT].epub",
        "title": "Date A Live - Volumen 08",
        "vol": "8"
    },
    # Vol 9
    "dPuP8tHgTX": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V09 [KPT].epub",
        "title": "Date A Live - Volumen 09",
        "vol": "9"
    },
    # Vol 10
    "LuHoLZkDbW": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V10 [KPT].epub",
        "title": "Date A Live - Volumen 10",
        "vol": "10"
    },
    # Vol 11
    "M3cHfjNQND": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V11 [KPT].epub",
        "title": "Date A Live - Volumen 11",
        "vol": "11"
    },
    # Vol 12
    "cxMzLjSDCw": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V12 [KPT].epub",
        "title": "Date A Live - Volumen 12",
        "vol": "12"
    },
    # Vol 13
    "OKmoa7gak3": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V13 [DALT].epub",
        "title": "Date A Live - Volumen 13",
        "vol": "13"
    },
    # Vol 14 (ya funciona con z0sOetvQH2)
    "z0sOetvQH2": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V14 [DALT & EHJR].epub",
        "title": "Date A Live - Volumen 14",
        "vol": "14"
    },
    # Vol 15
    "htE7qNgPCr": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V15 [EHJR].epub",
        "title": "Date A Live - Volumen 15",
        "vol": "15"
    },
    # Vol 16 (ya funciona con nqhRsqimCt)
    "nqhRsqimCt": {
        "file": "/library/Date a Live - Koushi Tachibana [NL]/Date A Live - V16 [EHJR].epub",
        "title": "Date A Live - Volumen 16",
        "vol": "16"
    },
}

async def fix_date_a_live():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        for h, data in DATE_A_LIVE_MAPPINGS.items():
            stmt = text("""
                INSERT INTO url_mappings (hash, url, book_title, series_name, volume_number, is_valid)
                VALUES (:hash, :url, :title, 'Date A Live', :volume, true)
                ON CONFLICT (hash) DO UPDATE SET
                    url = EXCLUDED.url,
                    book_title = EXCLUDED.book_title,
                    is_valid = true;
            """)
            await session.execute(stmt, {
                "hash": h,
                "url": data["file"],
                "title": data["title"],
                "volume": data["vol"]
            })
            print(f"✅ Mapeado: {h} -> Vol {data['vol']} ({data['file']})")
        await session.commit()

    print("\n🔍 Verificando estado HTTP de todos los 16 enlaces...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        all_ok = True
        for h, data in DATE_A_LIVE_MAPPINGS.items():
            url = f"https://dl.zeepubs.com/{h}"
            r = await client.get(url, follow_redirects=False)
            status = r.status_code
            cd = r.headers.get("content-disposition", "")
            fname = cd.split("filename=")[-1] if cd else ""
            print(f"[{status}] {url} (Vol {data['vol']}) -> {fname}")
            if status != 200:
                all_ok = False

        if all_ok:
            print("\n🎉 ¡TODOS LOS 16 ENLACES DE DATE A LIVE ESTÁN FUNCIONANDO AL 100%!")
        else:
            print("\n⚠️ Aún hay enlaces con errores.")

if __name__ == "__main__":
    asyncio.run(fix_date_a_live())
