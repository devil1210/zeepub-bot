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

    base_titulo = title.strip()
    base_titulo = re.sub(r"\[.*?\]", "", base_titulo)

    parts = re.split(r"(?:\s+[\-\–\—\−\―\~～\|¦║]\s+)|(?:\s*:\s*)", base_titulo)
    if parts:
        first_part = parts[0].strip()
        if len(first_part) <= 3 and len(parts) > 1:
            base_titulo = first_part + " " + parts[1].strip()
        else:
            base_titulo = first_part

    base_titulo = base_titulo.replace("×", "x")
    base_titulo = base_titulo.replace(",", " ")

    # Reemplazar caracteres con tildes y ñ por sus equivalentes básicos
    import unicodedata

    base_titulo = "".join(
        c
        for c in unicodedata.normalize("NFD", base_titulo)
        if unicodedata.category(c) != "Mn"
    )
    # Solo permitir letras latinas básicas, números y espacios
    base_titulo = re.sub(r"[^a-zA-Z0-9\s_]", "", base_titulo)
    # Reemplazar múltiples espacios por uno solo
    base_titulo = re.sub(r"\s+", " ", base_titulo).strip()
    # Capitalizar inicial de cada palabra y unir con _
    words = re.split(r"[\s_]+", base_titulo)
    capitalized_words = [w.capitalize() for w in words if w]
    slug = "_".join(capitalized_words)
    return slug


def format_published_date(date_str: str) -> str:
    """Formatea una fecha ISO o YYYY-MM-DD a formato legible DD-MM-YYYY."""
    if not date_str:
        return ""
    date_str = date_str.strip()

    # 1. Intentar parsear ISO con 'T'
    if "T" in date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d-%m-%Y")
        except (ValueError, TypeError):
            pass

    # 2. Intentar parsear como YYYY-MM-DD
    try:
        part = date_str[:10]
        if re.match(r"^\d{4}-\d{2}-\d{2}$", part):
            dt = datetime.strptime(part, "%Y-%m-%d")
            return dt.strftime("%d-%m-%Y")
    except (ValueError, TypeError):
        pass

    return date_str


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
        elif isinstance(tags, list):
            # Limpiar si contiene objetos Genre u otros modelos de base de datos
            tags = [t.name if hasattr(t, "name") else str(t) for t in tags]

        # Pre-formatear campos numéricos
        size_mb_val = data.get("size_mb") or data.get("size") or data.get("tamaño") or 0.0
        if isinstance(size_mb_val, str) and "mb" in size_mb_val.lower():
            size_mb_formatted = size_mb_val.strip()
        else:
            file_size = data.get("file_size") or data.get("fileSize")
            if file_size:
                try:
                    size_mb_formatted = f"{float(file_size) / (1024 * 1024):.2f} MB"
                except (ValueError, TypeError):
                    size_mb_formatted = str(file_size)
            else:
                try:
                    size_mb_formatted = f"{float(size_mb_val):.2f} MB"
                except (ValueError, TypeError):
                    size_mb_formatted = "0.00 MB"

        rating_average = data.get("rating_average") or 0.0
        rating_count = data.get("rating_count") or 0
        rating_txt = ""
        if rating_average and float(rating_average) > 0:
            rating_txt = f"\n⭐ {float(rating_average):.1f} ({rating_count} votos)"

        # Prioridad para el slug: el persistente de la DB (series_metadata)
        slug = data.get("slug")
        if not slug:
            slug_source = (
                data.get("series_name")
                or data.get("series")
                or data.get("serie")
                or data.get("titulo_serie")
                or data.get("clean_title")
                or data.get("title")
                or ""
            )
            slug = generate_slug_from_title(slug_source)

        published_at_raw = str(data.get("published_at") or data.get("fecha_publicacion") or data.get("fecha_publ") or "")
        published_at_formatted = format_published_date(published_at_raw)

        # Formatear fecha_modificacion también
        fecha_mod_raw = str(
            data.get("fecha")
            or data.get("fecha_actualizacion")
            or data.get("fecha_modificacion")
            or data.get("updated_at")
            or data.get("modified_at")
            or data.get("modified_at_opf")
            or ""
        )
        fecha_mod_formatted = format_published_date(fecha_mod_raw)

        volume_raw = data.get("volume")
        if volume_raw is None or volume_raw == "":
            volume_raw = data.get("series_index")
        if volume_raw is None or volume_raw == "":
            volume_raw = ""

        # Limpiar si contiene palabras como "Volumen", "Vol", "V"
        volume_str = str(volume_raw).strip()
        match_vol = re.search(
            r"(?:volumen|vol|v)\.?\s*0*(\d+(?:\.\d+)?)", volume_str, re.IGNORECASE
        )
        if match_vol:
            volume_str = match_vol.group(1)

        try:
            f = float(volume_str)
            volume_clean = str(int(f)) if f.is_integer() else str(f)
        except (ValueError, TypeError):
            volume_clean = volume_str

        # Sanitize demography and demographics (can be lists from JSONB)
        demography_raw = (
            data.get("demography")
            or data.get("demographics")
            or extract_demography(tags)
        )
        if isinstance(demography_raw, list):
            # Limpiar si contiene objetos Demographic u otros modelos de base de datos
            demography_raw = [d.name if hasattr(d, "name") else str(d) for d in demography_raw]
            demography_raw = ", ".join(demography_raw)

        demographics_raw = (
            data.get("demographics")
            or data.get("demography")
            or extract_demography(tags)
        )
        if isinstance(demographics_raw, list):
            # Limpiar si contiene objetos Demographic u otros modelos de base de datos
            demographics_raw = [d.name if hasattr(d, "name") else str(d) for d in demographics_raw]
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
            base_url = (
                config.DL_DOMAIN.rstrip("/")
                if config.DL_DOMAIN
                else config.BASE_URL.rstrip("/")
            )
            if base_url and not base_url.startswith("http"):
                base_url = f"https://{base_url}"
            download_link = f"{base_url}/{short_link}"

        # Formatear maquetadores como hashtags individuales (ej: "Zack, Saosora" -> "#Zack #Saosora")
        raw_layout = str(data.get("layout_by") or data.get("maquetador") or "").strip()
        if raw_layout:
            parts = [p.strip() for p in re.split(r"[,;]+|\s+(?=#)", raw_layout) if p.strip()]
            formatted_layout = " ".join(p if p.startswith("#") else f"#{p}" for p in parts)
        else:
            formatted_layout = ""

        mapping.update(
            {
                "titulo": data.get("title") or data.get("titulo") or "",
                "titulo_volumen": data.get("titulo_volumen") or data.get("title") or "",
                "romaji_title": data.get("romaji_title") or data.get("romaji") or "",
                "romaji": data.get("romaji") or data.get("romaji_title") or "",
                "jap_title": data.get("jap_title") or "",
                "slug": slug,
                "autor": data.get("author") or data.get("autor") or "",
                "author_jap": data.get("author_jap") or "",
                "illustrator": data.get("illustrator") or data.get("ilustrador") or "",
                "illustrator_jap": data.get("illustrator_jap") or "",
                "serie": data.get("serie")
                or data.get("series_english")
                or data.get("series")
                or data.get("titulo_serie")
                or "",
                "series": data.get("series")
                or data.get("serie")
                or data.get("series_english")
                or data.get("titulo_serie")
                or "",
                "series_english": data.get("series_english")
                or data.get("serie")
                or data.get("series")
                or data.get("titulo_serie")
                or "",
                "series_spanish": data.get("series_spanish")
                or data.get("series_name")
                or data.get("title")
                or data.get("titulo")
                or "",
                "volumen": volume_clean,
                "sinopsis": sinopsis_raw,
                "resumen": data.get("summary") or data.get("resumen") or "",
                "etiquetas": ", ".join(tags) if tags else "",
                "idioma": data.get("language") or data.get("idioma") or "",
                "traductor": data.get("traductor") or data.get("translator") or "",
                "translator": data.get("translator") or data.get("traductor") or "",
                "traductor_link": data.get("traductor_link") or data.get("grupo_link") or "",
                "traductor_web": data.get("traductor_web") or data.get("grupo_web") or "",
                "traductor_fb": data.get("traductor_fb") or data.get("grupo_fb") or "",
                "traductor_discord": data.get("traductor_discord") or data.get("grupo_discord") or "",
                "traductor_patreon": data.get("traductor_patreon") or data.get("grupo_patreon") or "",
                "traductor_twitter": data.get("traductor_twitter") or data.get("grupo_twitter") or "",
                "traductor_links": data.get("traductor_links") or data.get("grupo_links") or "",
                "grupo": data.get("grupo") or data.get("grupo_traductor") or "",
                "grupo_traductor": data.get("grupo_traductor") or data.get("grupo") or "",
                "grupo_link": data.get("grupo_link") or data.get("traductor_link") or "",
                "grupo_web": data.get("grupo_web") or data.get("traductor_web") or "",
                "grupo_fb": data.get("grupo_fb") or data.get("traductor_fb") or "",
                "grupo_discord": data.get("grupo_discord") or data.get("traductor_discord") or "",
                "grupo_patreon": data.get("grupo_patreon") or data.get("traductor_patreon") or "",
                "grupo_twitter": data.get("grupo_twitter") or data.get("traductor_twitter") or "",
                "grupo_links": data.get("grupo_links") or data.get("traductor_links") or "",
                "editor": data.get("editor") or data.get("corrector") or "",
                "editor_link": data.get("editor_link") or "",
                "editor_web": data.get("editor_web") or "",
                "editor_fb": data.get("editor_fb") or "",
                "editor_discord": data.get("editor_discord") or "",
                "editor_patreon": data.get("editor_patreon") or "",
                "editor_twitter": data.get("editor_twitter") or "",
                "editor_links": data.get("editor_links") or "",
                "maquetador": formatted_layout,
                "layout_by": formatted_layout,
                "maquetador_link": data.get("maquetador_link") or data.get("layout_link") or "",
                "maquetador_web": data.get("maquetador_web") or data.get("layout_web") or "",
                "maquetador_fb": data.get("maquetador_fb") or data.get("layout_fb") or "",
                "maquetador_discord": data.get("maquetador_discord") or data.get("layout_discord") or "",
                "maquetador_patreon": data.get("maquetador_patreon") or data.get("layout_patreon") or "",
                "maquetador_twitter": data.get("maquetador_twitter") or data.get("layout_twitter") or "",
                "maquetador_links": data.get("maquetador_links") or data.get("layout_links") or "",
                "tipo": data.get("book_type") or data.get("categoria") or "",
                "tamaño": size_mb_formatted,
                "size_mb": size_mb_formatted,
                "rating": str(rating_average),
                "rating_txt": rating_txt,
                "votes": str(rating_count),
                "hash": data.get("book_hash") or data.get("hash") or "",
                "version": data.get("epub_version") or "",
                "tags": ", ".join(tags) if tags else "",
                "genres": ", ".join(tags) if tags else "",
                "demography": demography_raw,
                "demographics": demographics_raw,
                "published_at": published_at_formatted,
                "fecha_publicacion": published_at_formatted,
                "fecha_publ": published_at_formatted,
                "fecha": fecha_mod_formatted or str(data.get("fecha", "")),
                "fecha_modificacion": fecha_mod_formatted,
                "updated_at": fecha_mod_formatted,
                "edition": data.get("edition") or "",
                "color_mode": data.get("color_mode") or "bw",
                "is_uncensored": "Sí" if data.get("is_uncensored") else "No",
                "isbn": data.get("isbn") or "",
                "asin": data.get("asin") or "",
                "palabras": str(data.get("palabras") or data.get("words") or data.get("word_count") or ""),
                "words": str(data.get("words") or data.get("palabras") or data.get("word_count") or ""),
                "paginas": str(data.get("paginas") or data.get("pages") or data.get("page_count") or ""),
                "pages": str(data.get("pages") or data.get("paginas") or data.get("page_count") or ""),
                "archivo": "__ATTACH_FILE_SIGNAL__",  # Marcador para que el Publisher sepa que debe adjuntar el archivo
                "nombre_archivo": (lambda f: f[: f.rfind(".")] if "." in f else f)(
                    data.get("filename") or "archivo.epub"
                ),
                "titulo_serie": data.get("series") or data.get("titulo_serie") or "",
                "fecha_actualizacion": data.get("fecha_actualizacion")
                or data.get("updated_at")
                or data.get("fecha_modificacion")
                or fecha_mod_formatted,
                "descargas_globales": str(
                    data.get("descargas_globales") or data.get("total_downloads") or 0
                ),
                "download_link": download_link,
            }
        )

        # Normalizar None a strings vacíos y asegurar string
        for k, v in list(mapping.items()):
            if v is None:
                mapping[k] = ""
            elif not isinstance(v, str):
                mapping[k] = str(v)

        # 2. Evaluar condicionales: [?variable]...[/?] y [?!variable]...[/?]
        def evaluate_conditional(match):
            raw_var = match.group(1).lower()
            content = match.group(2)
            is_negated = raw_var.startswith("!")
            var_name = raw_var[1:] if is_negated else raw_var
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
            is_empty = not value or value.lower() in not_found_values

            if is_negated:
                return content if is_empty else ""
            else:
                return "" if is_empty else content

        # Permitir condicionales anidados evaluando en loop hasta que no queden
        result_str = template_str
        for _ in range(5):
            new_str = re.sub(
                r"\[\?(!?\w+)\](.*?)\[/\?\]",
                evaluate_conditional,
                result_str,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if new_str == result_str:
                break
            result_str = new_str

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

        # Normalizar hashtags duplicados (ej: ##Zack -> #Zack)
        result_str = re.sub(r"#+#", "#", result_str)

        import html

        return html.unescape(result_str)

    except Exception as e:
        import logging
        logging.getLogger(__name__).exception(f"Error aplicando plantilla de publicación: {e}")
        # Fallback silencioso al string original
        return template_str
