import re
from datetime import datetime
from typing import Any


def extract_demography(tags: list) -> str:
    """Extrae la demografía de una lista de tags."""
    if not tags or not isinstance(tags, list):
        return ""
    demography_map = ["Seinen", "Shounen", "Shoujo", "Josei", "Kodomo"]
    for tag in tags:
        if tag in demography_map:
            return tag
    return ""


def generate_slug_from_title(title: str) -> str:
    """Genera un slug amigable desde un título."""
    if not title:
        return ""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "_", slug)
    slug = re.sub(r"-+", "_", slug)
    return slug.strip("_")[:50]


def format_published_date(date_str: str) -> str:
    """Formatea una fecha ISO a formato legible DD-MM-YYYY."""
    if not date_str:
        return ""
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d-%m-%Y")
    except (ValueError, TypeError):
        pass
    return date_str[:10] if len(date_str) >= 10 else date_str


def apply_publication_template(template_str: str, data: dict[str, Any]) -> str:
    """
    Aplica condicionales [?var]...[/?] y placeholders {var} con campos de Libro.
    Lógica compartida entre PublisherService y DeliveryService.
    """
    if not template_str:
        return ""

    try:
        # 1. Preparar mapping de datos
        mapping = {k: v for k, v in data.items()}

        # Enriquecer con nombres comunes usados en plantillas
        tags = data.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        # Pre-formatear campos numéricos
        size_mb_val = data.get("size_mb") or data.get("size") or 0.0
        if not size_mb_val or (isinstance(size_mb_val, str) and "mb" in size_mb_val.lower()):
            file_size = data.get("file_size") or data.get("fileSize") or 0
            if file_size:
                size_mb_val = file_size / (1024 * 1024)
            elif isinstance(size_mb_val, str):
                # Intentar limpiar el string si viene con "MB"
                try:
                    size_mb_val = float(re.sub(r"[^\d.]", "", size_mb_val))
                except (ValueError, TypeError):
                    size_mb_val = 0.0

        try:
            size_mb_formatted = f"{float(size_mb_val):.2f} MB"
        except (ValueError, TypeError):
            size_mb_formatted = "0.00 MB"

        rating_avg = data.get("rating_average") or 0.0
        rating_count = data.get("rating_count") or 0
        rating_txt = ""
        if rating_avg and float(rating_avg) > 0:
            rating_txt = f"\n⭐ {float(rating_avg):.1f} ({rating_count} votos)"

        # Prioridad para el slug: el persistente de la DB (series_metadata)
        slug = data.get("slug")
        if not slug:
            slug_source = (
                data.get("series_english")
                or data.get("series")
                or data.get("serie")
                or data.get("series_spanish")
                or data.get("titulo_serie")
                or data.get("clean_title")
                or data.get("title")
                or ""
            )
            slug = generate_slug_from_title(slug_source)

        published_at_raw = str(data.get("published_at") or "")
        published_at_formatted = format_published_date(published_at_raw)

        # Formatear fecha_modificacion también
        fecha_mod_raw = str(data.get("fecha_modificacion") or data.get("updated_at") or data.get("modified_at") or "")
        fecha_mod_formatted = format_published_date(fecha_mod_raw)

        volume_raw = data.get("volume") or data.get("series_index") or ""
        volume_clean = (
            str(int(float(volume_raw)))
            if volume_raw and str(volume_raw).replace(".", "").replace("-", "").isdigit()
            else str(volume_raw)
        )

        # Sanitize demography and demographics (can be lists from JSONB)
        demography_raw = data.get("demography") or data.get("demographics") or extract_demography(tags)
        if isinstance(demography_raw, list):
            demography_raw = ", ".join(demography_raw)

        demographics_raw = data.get("demographics") or data.get("demography") or extract_demography(tags)
        if isinstance(demographics_raw, list):
            demographics_raw = ", ".join(demographics_raw)

        # Sanitize sinopsis - remove HTML tags not supported by Telegram
        sinopsis_raw = data.get("description") or data.get("sinopsis") or ""
        if sinopsis_raw:
            sinopsis_raw = re.sub(r"<p[^>]*>", "", sinopsis_raw, flags=re.IGNORECASE)
            sinopsis_raw = re.sub(r"</p>", "\n", sinopsis_raw, flags=re.IGNORECASE)
            sinopsis_raw = re.sub(r"<div[^>]*>", "", sinopsis_raw, flags=re.IGNORECASE)
            sinopsis_raw = re.sub(r"</div>", "", sinopsis_raw, flags=re.IGNORECASE)
            sinopsis_raw = re.sub(r"<span[^>]*>", "", sinopsis_raw, flags=re.IGNORECASE)
            sinopsis_raw = re.sub(r"</span>", "", sinopsis_raw, flags=re.IGNORECASE)
            sinopsis_raw = re.sub(r"<br\s*/?>", "\n", sinopsis_raw, flags=re.IGNORECASE)
            sinopsis_raw = re.sub(r"\n{3,}", "\n\n", sinopsis_raw).strip()

        from config.config_settings import config

        download_link = ""
        short_link = data.get("short_link")
        if short_link:
            base_url = config.DL_DOMAIN.rstrip("/") if config.DL_DOMAIN else config.BASE_URL.rstrip("/")
            if base_url and not base_url.startswith("http"):
                base_url = f"https://{base_url}"
            download_link = f"{base_url}/{short_link}"

        mapping.update(
            {
                "titulo": data.get("title") or data.get("titulo") or "",
                "titulo_volumen": data.get("titulo_volumen") or data.get("title") or "",
                "romaji_title": data.get("romaji_title") or "",
                "english_title": data.get("english_title") or "",
                "spanish_title": data.get("spanish_title") or "",
                "jap_title": data.get("jap_title") or "",
                "slug": slug,
                "autor": data.get("author") or data.get("autor") or "",
                "author_jap": data.get("author_jap") or "",
                "illustrator": data.get("illustrator") or data.get("ilustrador") or "",
                "illustrator_jap": data.get("illustrator_jap") or "",
                "serie": data.get("series") or data.get("titulo_serie") or "",
                "series_spanish": data.get("series_spanish") or "",
                "series_english": data.get("series_english") or "",
                "volumen": volume_clean,
                "sinopsis": sinopsis_raw,
                "resumen": data.get("summary") or data.get("resumen") or "",
                "etiquetas": ", ".join(tags) if tags else "",
                "idioma": data.get("language") or data.get("idioma") or "",
                "editorial": data.get("publisher") or data.get("editorial") or "",
                "traductor": data.get("translator") or data.get("traductor") or "",
                "maquetador": data.get("layout_by") or data.get("maquetador") or "",
                "layout_by": data.get("layout_by") or data.get("maquetador") or "",
                "tipo": data.get("book_type") or data.get("categoria") or "",
                "tamaño": size_mb_formatted,
                "size_mb": size_mb_formatted,
                "rating": str(rating_avg),
                "rating_txt": rating_txt,
                "votes": str(rating_count),
                "hash": data.get("book_hash") or data.get("hash") or "",
                "version": data.get("epub_version") or "",
                "tags": ", ".join(tags) if tags else "",
                "genres": ", ".join(tags) if tags else "",
                "demography": demography_raw,
                "demographics": demographics_raw,
                "published_at": published_at_formatted,
                "fecha": fecha_mod_formatted,
                "fecha_modificacion": fecha_mod_formatted,
                "updated_at": fecha_mod_formatted,
                "edition": data.get("edition") or "",
                "color_mode": data.get("color_mode") or "bw",
                "is_uncensored": "Sí" if data.get("is_uncensored") else "No",
                "isbn": data.get("isbn") or "",
                "asin": data.get("asin") or "",
                "archivo": "",  # Se deja vacío para que no se imprima como texto (se maneja como adjunto)
                "titulo_serie": data.get("series") or data.get("titulo_serie") or "",
                "fecha_actualizacion": data.get("updated_at") or data.get("fecha_modificacion") or fecha_mod_formatted,
                "descargas_globales": str(data.get("descargas_globales") or data.get("total_downloads") or 0),
                "download_link": download_link,
            }
        )

        # Normalizar None a strings vacíos y asegurar string
        for k, v in list(mapping.items()):
            if v is None:
                mapping[k] = ""
            elif not isinstance(v, str):
                mapping[k] = str(v)

        # 2. Evaluar condicionales: [?variable]...[/?]
        def evaluate_conditional(match):
            var_name = match.group(1).lower()
            content = match.group(2)
            value = mapping.get(var_name, "").strip()

            # Considerar vacío si es Desconocido, 0.0, 0 MB o string vacío
            not_found_values = [
                "",
                "desconocido",
                "desconocida",
                "0.0",
                "0",
                "0.00 mb",
                "0 mb",
                "false",
                "none",
                "no",
            ]
            if not value or value.lower() in not_found_values:
                return ""
            return content

        # Regex DOTALL para permitir saltos de línea dentro del condicional
        result_str = re.sub(
            r"\[\?(\w+)\](.*?)\[/\?\]",
            evaluate_conditional,
            template_str,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # 3. Reemplazos directos {var}
        # Manejar {var:.2f} y similares eliminando el formato (ya que pre-formateamos)
        result_str = re.sub(r"\{(\w+):.*?\}", r"{\1}", result_str)

        placeholders = set(re.findall(r"\{(\w+)\}", result_str))
        for p in placeholders:
            val = mapping.get(p, "")
            # Valores por defecto visuales solo para la renderización normal
            if not val and p == "autor":
                val = "Desconocido"
            elif not val and (p == "tamaño" or p == "size_mb"):
                val = "0.00 MB"
            result_str = result_str.replace(f"{{{p}}}", val)

        # Limpiar saltos de línea triples generados por condicionales vacíos
        result_str = re.sub(r"\n{3,}", "\n\n", result_str).strip()

        return result_str

    except Exception:
        # Fallback silencioso al string original
        return template_str
