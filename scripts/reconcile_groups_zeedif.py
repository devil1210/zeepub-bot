# scripts/reconcile_groups_zeedif.py
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.library import TranslatorsGroup


def parse_zeedif_markdown(md_path: str = "") -> list[dict]:
    """Extrae las filas de la tabla de editoriales de Zeedif."""
    try:
        from scripts.reconcile_dict import MAPPING_ZEEDIF

        return [{"name": k, "tag": v, "books": "0"} for k, v in MAPPING_ZEEDIF.items()]
    except ImportError:
        pass
    entries = []

    if not os.path.exists(md_path):
        print(f"Archivo no encontrado: {md_path}")
        return []

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = []
    table_started = False
    for line in lines:
        line = line.strip()
        if line.startswith("| Editorial |"):
            table_started = True
            continue
        if table_started and line.startswith("|---"):
            continue
        if table_started and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 2:
                name = parts[0]
                tag = parts[1]
                books = parts[2] if len(parts) > 2 else "0"
                if name and name != "—" and tag and tag != "—":
                    entries.append({"name": name, "tag": tag, "books": books})
        elif table_started and not line.startswith("|") and line:
            # Termina la tabla
            break

    return entries


async def reconcile():
    md_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "editoriales_zeedif.md",
    )
    zeedif_entries = parse_zeedif_markdown(md_path)
    print(f"📖 Entradas leídas del markdown de Zeedif: {len(zeedif_entries)}")

    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res = await session.execute(select(TranslatorsGroup))
        db_groups = res.scalars().all()
        print(f"💾 Grupos actualmente en BD: {len(db_groups)}")

        db_map_name = {g.name.lower().strip(): g for g in db_groups}

        matched = 0
        updated = 0
        new_groups = 0

        for item in zeedif_entries:
            name = item["name"]
            tag = item["tag"]
            g = db_map_name.get(name.lower().strip())
            if g:
                matched += 1
                if not g.siglas or g.siglas != tag:
                    print(
                        f"  ✏️ Actualizando siglas para '{g.name}': '{g.siglas}' -> '{tag}'"
                    )
                    g.siglas = tag
                    updated += 1
            else:
                # Ver si hay coincidencia parcial
                partial = [
                    db_g
                    for db_g in db_groups
                    if db_g.name.lower().startswith(name.lower()[:5])
                ]
                if partial:
                    print(
                        f"  🔍 Coincidencia aproximada para '{name}': {partial[0].name}"
                    )
                else:
                    print(f"  ➕ Nuevo grupo no registrado: '{name}' con sigla '{tag}'")
                    new_g = TranslatorsGroup(name=name, siglas=tag)
                    session.add(new_g)
                    new_groups += 1

        await session.commit()
        print(
            f"\n✅ Conciliación terminada: {matched} encontrados, {updated} siglas actualizadas, {new_groups} nuevos grupos creados."
        )


if __name__ == "__main__":
    asyncio.run(reconcile())
