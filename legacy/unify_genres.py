import asyncio
import json
from sqlalchemy import text
from core.db_manager_pg import pg_manager

MAPPING = {
    # Acción y derivados
    "Accion": "Acción",
    "Action": "Acción",
    "Accion ": "Acción",
    "Acción": "Acción",
    "Accin": "Acción",
    "Acci\u00f3n": "Acción",
    # Ciencia Ficción
    "Ciencia Ficcion": "Ciencia Ficción",
    "Ciencia ficción": "Ciencia Ficción",
    "Ciencia Ficcin": "Ciencia Ficción",
    "Sci-Fi": "Ciencia Ficción",
    "SciFi": "Ciencia Ficción",
    "Sci Fi": "Ciencia Ficción",
    "Ciencia Ficción": "Ciencia Ficción",
    "C. Ficción": "Ciencia Ficción",
    # Fantasía
    "Fantasia": "Fantasía",
    "Fantasy": "Fantasía",
    "Fantasía": "Fantasía",
    "Fantasa": "Fantasía",
    "Fantas\u00eda": "Fantasía",
    # Erótico / Ecchi
    "Erotico": "Erótico",
    "Erotismo": "Erótico",
    "Erótico": "Erótico",
    "Erotio": "Erótico",
    "Adulto": "Erótico",
    "Ecchi": "Ecchi",
    "Echi": "Ecchi",
    # Recuentos de la Vida
    "Recuentos de la vida": "Recuentos de la Vida",
    "Recuentos de la Vida": "Recuentos de la Vida",
    "Slice of Life": "Recuentos de la Vida",
    "Vida Diaria": "Recuentos de la Vida",
    # Otros frecuentes
    "Jovenil": "Juvenil",
    "Juvenil": "Juvenil",
    "Mystery": "Misterio",
    "Mistery": "Misterio",
    "Misterio": "Misterio",
    "Adventure": "Aventura",
    "Aventura": "Aventura",
    "Psychological": "Psicológico",
    "Psicologico": "Psicológico",
    "Psicológico": "Psicológico",
    "Psicolgo": "Psicológico",
    "Supernatural": "Sobrenatural",
    "Sobrenatural": "Sobrenatural",
    "Horror": "Terror",
    "Terror": "Terror",
    "Tragedy": "Tragedia",
    "Tragedia": "Tragedia",
    "Martial Arts": "Artes Marciales",
    "Artes Marciales": "Artes Marciales",
    "Sports": "Deporte",
    "Deporte": "Deporte",
    "School": "Escolar",
    "Escolar": "Escolar",
    "Comedy": "Comedia",
    "Comedia": "Comedia",
    "Drama": "Drama",
    "Harem": "Harén",
    "Harén": "Harén",
    "Haren": "Harén",
    "Romance": "Romance",
    "Amor": "Romance",
    "Isekai": "Isekai",
    "Reencarnación": "Isekai",
    "Reencarnacion": "Isekai",
    # Demográficos
    "Shounen": "Shounen",
    "Seinen": "Seinen",
    "Shoujo": "Shoujo",
    "Josei": "Josei",
    "Kodomo": "Kodomo",
    "Historical": "Histórico",
    "Historico": "Histórico",
    "Histórico": "Histórico",
    "Military": "Militar",
    "Militar": "Militar",
    "Magic": "Magia",
    "Magia": "Magia",
    "Mecha": "Mecha",
    # Mapeos especiales
    "Chicos": "Shounen",  # "Chicos" es demografía (Shounen), lo normalizamos así
}


def normalize_str(s):
    import unicodedata

    if not s:
        return ""
    # Remove accents and special quotes
    s = s.replace("´", "").replace("`", "").replace("'", "")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


async def unify_genres():
    print("🚀 Iniciando unificación de géneros...")
    async with pg_manager.get_session() as session:
        print("🔍 Consultando serie_metadata...")
        res = await session.execute(text("SELECT id, series_hash, tags, demographics, series_name FROM series_metadata"))
        print("✅ Consulta enviada. Procesando por lotes...")
        
        updates = 0
        updated_series_hashes = []

        normalized_mapping = {}
        for k, v in MAPPING.items():
            normalized_mapping[normalize_str(k)] = v

        while True:
            rows = res.fetchmany(100)
            if not rows:
                break
            
            print(f"📦 Procesando lote de {len(rows)} series...")
            for row_id, s_hash, tags_raw, demo_raw, series_name in rows:
                def process_list(raw, is_demographics=False):
                    if not raw:
                        return [], False, []
                    items = raw if isinstance(raw, list) else []
                    if not items and isinstance(raw, str) and raw.strip():
                        try:
                            items = json.loads(raw)
                        except Exception:
                            return [], False, []
                    if not isinstance(items, list):
                        return [], False, []

                    new_set = set()
                    changed_item = False
                    
                    # Para rastrear si debemos mover algo de tags a demographics
                    items_to_move = []

                    for t in items:
                        if not t: continue
                        t_str = str(t).strip()
                        t_norm = normalize_str(t_str)

                        if t_norm in normalized_mapping:
                            unified = normalized_mapping[t_norm]
                            
                            # Caso especial: "Chicos" se mueve a demografía si estamos en tags
                            if t_norm == normalize_str("Chicos") and not is_demographics:
                                items_to_move.append("Shounen")
                                changed_item = True
                                continue

                            if unified:
                                new_set.add(unified)
                                if unified != t_str:
                                    changed_item = True
                            else:
                                # Si el mapeo es None, simplemente descartamos
                                changed_item = True
                            continue

                        # Handle slashes like "Action / Adventure"
                        if "/" in t_str:
                            parts = [p.strip() for p in t_str.split("/")]
                            for p in parts:
                                p_n = normalize_str(p)
                                if p_n in normalized_mapping:
                                    unified_p = normalized_mapping[p_n]
                                    if unified_p:
                                        new_set.add(unified_p)
                                    changed_item = True
                                else:
                                    new_set.add(p)
                            continue

                        new_set.add(t_str)

                    final = sorted(list(new_set))
                    original = sorted([str(x).strip() for x in items if x])
                    return final, (final != original), items_to_move

                new_tags, tags_changed, to_demo = process_list(tags_raw, is_demographics=False)
                new_demos, demos_changed, _ = process_list(demo_raw, is_demographics=True)

                # Si hay items para mover a demografía, añadirlos a new_demos
                if to_demo:
                    demo_set = set(new_demos)
                    for d in to_demo:
                        if d not in demo_set:
                            demo_set.add(d)
                            demos_changed = True
                    new_demos = sorted(list(demo_set))

                if tags_changed or demos_changed:
                    print(f"  💾 Corrigiendo: {series_name}")
                    stmt = text("UPDATE series_metadata SET tags = :tags, demographics = :demos, updated_at = NOW() WHERE id = :id")
                    await session.execute(
                        stmt, {"tags": json.dumps(new_tags), "demos": json.dumps(new_demos), "id": row_id}
                    )

                    # Registrar en auditoría para revisión en Admin Panel
                    audit_stmt = text("""
                        INSERT INTO metadata_audits (series_hash, series_name, change_type, old_value, new_value)
                        VALUES (:hash, :name, :type, :old, :new)
                    """)
                    await session.execute(audit_stmt, {
                        "hash": s_hash,
                        "name": series_name,
                        "type": "genre_unification",
                        "old": json.dumps({"tags": tags_raw, "demographics": demo_raw}),
                        "new": json.dumps({"tags": new_tags, "demographics": new_demos})
                    })
                    updates += 1
                    updated_series_hashes.append(s_hash)

        if updates > 0:
            await session.commit()
            print(f"✅ Se actualizaron {updates} series.")
            
            # Generar reporte de volúmenes
            print("\n📋 Generando reporte de volúmenes afectados...")
            v_res = await session.execute(
                text("""
                    SELECT series_info.series_name, lb.volume, lb.title, lb.layout_by
                    FROM local_books lb
                    JOIN series_metadata series_info ON lb.series_hash = series_info.series_hash
                    WHERE lb.series_hash = ANY(:hashes)
                    ORDER BY series_info.series_name ASC, lb.volume ASC
                """),
                {"hashes": updated_series_hashes}
            )
            v_rows = v_res.fetchall()
            
            if v_rows:
                report_content = "# 📋 Reporte de Corrección de Géneros\n\n"
                report_content += "Se han detectado y corregido inconsistencias en los géneros/demografía de las siguientes series. Este reporte debe ser revisado por los maquetadores.\n\n"
                report_content += "| Serie | Vol | Título | Maquetador |\n"
                report_content += "| :--- | :--- | :--- | :--- |\n"
                for v in v_rows:
                    report_content += f"| {v[0]} | {v[1]} | {v[2]} | {v[3] or 'Desconocido'} |\n"
                
                with open("genre_correction_report.md", "w", encoding="utf-8") as f:
                    f.write(report_content)
                
                print("\n" + report_content)
                print(f"\n✅ Reporte guardado en 'genre_correction_report.md'")
            else:
                print("No se encontraron volúmenes asociados a las series corregidas.")
        else:
            print("✨ No se detectaron géneros que requieran corrección.")


if __name__ == "__main__":
    asyncio.run(unify_genres())
