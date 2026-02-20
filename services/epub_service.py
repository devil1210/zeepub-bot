# services/epub_service.py

import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Any

from utils.helpers import limpiar_html_basico


def extract_internal_title(data_or_path: bytes | str) -> str | None:
    """
    Busca un título interno en archivos 'title' o 'titulo' dentro del EPUB.
    Prioriza <... epub:type="fulltitle"> y combina title/subtitle.
    Fallback a <span class="grande" epub:type="title">.
    """
    try:
        if isinstance(data_or_path, (bytes, bytearray)):
            zf = zipfile.ZipFile(io.BytesIO(data_or_path))
        else:
            zf = zipfile.ZipFile(data_or_path)

        # Buscar archivos candidatos
        candidates = [n for n in zf.namelist() if "title" in n.lower() or "titulo" in n.lower()]

        # Regex para fulltitle: <tag ... epub:type="fulltitle" ...> content </tag>
        fulltitle_pattern = re.compile(
            r'<(\w+)[^>]*epub:type="fulltitle"[^>]*>(.*?)</\1>',
            re.IGNORECASE | re.DOTALL,
        )

        # Regex para componentes internos
        title_pat = re.compile(r'epub:type="title"[^>]*>(.*?)<', re.IGNORECASE | re.DOTALL)
        subtitle_pat = re.compile(r'epub:type="subtitle"[^>]*>(.*?)<', re.IGNORECASE | re.DOTALL)

        # Regex legacy/fallback
        pattern_legacy = re.compile(
            r'<span[^>]*class="grande"[^>]*epub:type="title"[^>]*>(.*?)</span>',
            re.IGNORECASE | re.DOTALL,
        )
        pattern_loose = re.compile(r'<span[^>]*epub:type="title"[^>]*>(.*?)</span>', re.IGNORECASE | re.DOTALL)

        for name in candidates:
            try:
                content = zf.read(name).decode("utf-8", errors="ignore")

                # Remove HTML comments first to avoid matching commented-out tags
                content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

                # 1. Intentar fulltitle
                match = fulltitle_pattern.search(content)
                if match:
                    inner_html = match.group(2)

                    # Buscar title y subtitle dentro
                    t_match = title_pat.search(inner_html)
                    s_match = subtitle_pat.search(inner_html)

                    if t_match and s_match:
                        t_text = re.sub(r"<[^>]+>", "", t_match.group(1)).strip()
                        s_text = re.sub(r"<[^>]+>", "", s_match.group(1)).strip()

                        if t_text and s_text:
                            # Agregar separador si no existe
                            if not t_text.endswith(":") and not t_text.endswith("-"):
                                return f"{t_text}: {s_text}"
                            return f"{t_text} {s_text}"

                    # Si no hay sub-tags claros, limpiar HTML (reemplazando br con espacio)
                    clean = re.sub(r"<br\s*/?>", " ", inner_html, flags=re.IGNORECASE)
                    clean = re.sub(r"<[^>]+>", "", clean).strip()
                    clean = clean.replace("-->", "").strip()
                    clean = " ".join(clean.split())
                    if clean:
                        return clean

                # 2. Fallback a lógica anterior
                match = pattern_legacy.search(content)
                if not match:
                    match = pattern_loose.search(content)

                if match:
                    text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
                    return text
            except Exception:
                continue

        return None
    except Exception:
        return None


async def parse_opf_from_epub(data_or_path: bytes | str) -> dict[str, Any]:
    """
    Extrae metadatos OPF de un EPUB (bytes o ruta) usando namespaces y heurísticas.
    Retorna dict con claves:
      titulo_volumen, titulo_serie, autores (list), ilustrador, generos (list),
      demografia (list), categoria, maquetadores (list), traductor, publisher,
      publisher_url, sinopsis.
    """

    def _read_opf(z: zipfile.ZipFile) -> bytes | None:
        # Leer container.xml para ubicar el .opf
        try:
            container = z.read("META-INF/container.xml")
            tree = ET.fromstring(container)
            for rf in tree.findall(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"):
                path = rf.attrib.get("full-path", "")
                if path.lower().endswith(".opf"):
                    return z.read(path)
        except Exception:
            pass
        # Fallback: primer .opf en el zip
        for name in z.namelist():
            if name.lower().endswith(".opf"):
                return z.read(name)
        return None

    def local_name(elem: ET.Element) -> str:
        tag = elem.tag
        return tag.split("}", 1)[-1] if "}" in tag else tag

    def local_name_attr(attr_name: str) -> str:
        return attr_name.split("}", 1)[-1] if "}" in attr_name else attr_name

    def parse_date(raw_date: str) -> str | None:
        if not raw_date:
            return None
        try:
            # Basic cleanup and separator normalization
            clean = raw_date.strip().replace("/", "-").split("T")[0]
            parts = clean.split("-")

            y, m, d = 0, 0, 0

            if len(parts) == 3:
                p0, p1, p2 = parts[0], parts[1], parts[2]

                # Case 1: YYYY-MM-DD (e.g. 2022-07-01 or 2022-007-01)
                if len(p0) == 4 and p0.isdigit():
                    y, m, d = int(p0), int(p1), int(p2)

                    # Fix: Handle YYYY-DD-MM (e.g. 2019-28-12)
                    # If month is obviously wrong (>12) and day looks like a month (<=12), swap them
                    if m > 12 >= d:
                        m, d = d, m
                    # Or if month is just > 12, assume it's the day (heuristic)
                    elif m > 12:
                        m, d = d, m

                # Case 2: DD-MM-YYYY (e.g. 01-07-2022)
                elif len(p2) == 4 and p2.isdigit():
                    y, m, d = int(p2), int(p1), int(p0)

            # Case 3: YYYY Only
            elif len(parts) == 1 and len(parts[0]) == 4 and parts[0].isdigit():
                y = int(parts[0])
                m, d = 1, 1

            # Validate and Format
            if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"

        except Exception:
            pass

        return None  # Return None on failure to avoid DB TypeErrors

    def _parse_opf(data: bytes) -> dict[str, Any]:
        import logging

        logger = logging.getLogger(__name__)

        root = ET.fromstring(data)
        out: dict[str, Any] = {
            "titulo_volumen": None,
            "titulo_serie": None,
            "volume_index": None,
            "autores": [],
            "ilustrador": None,
            "generos": [],
            "demografia": [],
            "categoria": None,
            "maquetadores": [],
            "traductor": None,
            "publisher": None,
            "publisher_url": None,
            "sinopsis": None,
            "epub_version": None,
            "fecha_modificacion": None,
            "fecha_publicacion": None,
            "is_uncensored": 0,
            "color_mode": "bw",
            "isbn": None,
        }

        # Version EPUB: <package version="...">
        # root es el elemento <package>
        version = root.attrib.get("version")
        out["epub_version"] = version
        logger.debug(f"EPUB version extracted: {version}")

        # Fecha modificación: dcterms:modified
        # Ejemplo: <meta property="dcterms:modified">2022-07-03T10:28:12Z</meta>
        for el in root.iter():
            ln = local_name(el).lower()
            if ln == "meta":
                # Obtener atributos property y name ignorando namespaces
                attribs = {local_name_attr(k).lower(): v for k, v in el.attrib.items()}
                prop = attribs.get("property", "")
                name = attribs.get("name", "")

                if "modified" in prop or "modified" in name:
                    if el.text:
                        raw_date = el.text.strip()
                        out["fecha_modificacion"] = parse_date(raw_date)
                        logger.debug(f"Modified date found: {raw_date} -> {out['fecha_modificacion']}")
                        break

        # Fecha publicación: dc:date
        # Ejemplo: <dc:date>2020-07-02T00:00:00Z</dc:date>
        for el in root.iter():
            ln = local_name(el).lower()
            if ln == "date":
                # Verificar si es dc:date (aunque local_name ya lo filtra, aseguramos que sea fecha)
                if el.text:
                    raw_date = el.text.strip()
                    # Si ya tenemos una fecha, solo sobrescribimos si el evento es 'publication'
                    attribs = {local_name_attr(k).lower(): v for k, v in el.attrib.items()}
                    event = attribs.get("event", "")

                    parsed = parse_date(raw_date)
                    if not out["fecha_publicacion"]:
                        out["fecha_publicacion"] = parsed
                        logger.debug(f"Publication date found: {raw_date} -> {parsed}")
                    elif event == "publication":
                        out["fecha_publicacion"] = parsed
                        logger.debug(f"Publication date (event=publication) found: {raw_date} -> {parsed}")
                        break

        # Título volumen: primer <dc:title> o <title>
        for el in root.iter():
            if local_name(el).lower() == "title" and el.text:
                out["titulo_volumen"] = el.text.strip()
                break

        # Metadata extendida: Series y Volumen Index
        collection_ids = {}  # id -> title (para refines)

        # Primera pasada: Recolectar Series ID si existen
        for el in root.iter():
            if local_name(el).lower() == "meta":
                prop = el.attrib.get("property", "") or el.attrib.get("{http://www.idpf.org/2007/opf}property", "")
                if prop == "belongs-to-collection" and el.text:
                    out["titulo_serie"] = el.text.strip()
                    if el.attrib.get("id"):
                        collection_ids[el.attrib.get("id")] = out["titulo_serie"]

        # Segunda pasada: Otras propiedades
        for el in root.iter():
            if local_name(el).lower() == "meta":
                attribs = {local_name_attr(k).lower(): v for k, v in el.attrib.items()}
                prop = attribs.get("property", "")
                name = attribs.get("name", "")
                content = attribs.get("content", "")
                text_val = el.text.strip() if el.text else ""

                # Fallback Series (Calibre)
                if name == "calibre:series" and not out["titulo_serie"]:
                    out["titulo_serie"] = content

                # Volume Index
                # 1. group-position (Standard EPUB3)
                if prop == "group-position":
                    # Check refines match if strictly needed, or just take it if simple
                    refines = attribs.get("refines", "").replace("#", "")
                    if not refines or refines in collection_ids or not collection_ids:
                        # Si no hay refines, o coincide con la serie detectada
                        try:
                            out["volume_index"] = float(text_val)
                        except Exception:
                            pass

                # 2. calibre:series_index
                elif name == "calibre:series_index":
                    try:
                        out["volume_index"] = float(content)
                    except Exception:
                        pass

        # Creators & contributors
        contributors = []
        id_to_name: dict[str, str] = {}
        for el in root.iter():
            ln = local_name(el).lower()
            if ln in ("creator", "dc:creator"):
                text = (el.text or "").strip()
                if text:
                    out["autores"].append(text)
                cid = el.attrib.get("id")
                if cid and text:
                    id_to_name[cid] = text
            elif ln in ("contributor", "dc:contributor"):
                text = (el.text or "").strip()
                if text:
                    contributors.append(text)
                cid = el.attrib.get("id")
                if cid and text:
                    id_to_name[cid] = text

        # Subjects => géneros y demografía
        subjects = [
            (el.text or "").strip()
            for el in root.iter()
            if local_name(el).lower() in ("subject", "dc:subject") and el.text
        ]
        dem_keys = {"seinen", "shounen", "shônen", "shoujo", "josei", "juvenil"}
        for s in subjects:
            if any(k in s.lower() for k in dem_keys):
                out["demografia"].append(s)
            else:
                out["generos"].append(s)

        # Edition characteristics (Options 1 & 3)
        all_subjects = " ".join(subjects).lower()
        if any(x in all_subjects for x in ["sin censura", "uncensored", "no censura"]):
            out["is_uncensored"] = 1

        if any(x in all_subjects for x in ["ilustraciones a color", "color", "full color"]):
            out["color_mode"] = "color"
        elif any(x in all_subjects for x in ["blanco y negro", "b&w", "grayscale", "b/n"]):
            out["color_mode"] = "bw"

        # Meta properties Zeepub
        for el in root.iter():
            if local_name(el).lower() == "meta":
                attribs = {local_name_attr(k).lower(): v for k, v in el.attrib.items()}
                prop = attribs.get("property", "").lower()
                name = attribs.get("name", "").lower()
                content = attribs.get("content", "")

                if "zeepub:uncensored" in prop or "zeepub:uncensored" in name:
                    val = (content or el.text or "").lower().strip()
                    if val in ["true", "1", "yes"]:
                        out["is_uncensored"] = 1
                if "zeepub:color_mode" in prop or "zeepub:color_mode" in name:
                    val = (content or el.text or "").lower().strip()
                    if val in ["color", "full-color", "c"]:
                        out["color_mode"] = "color"
                    elif val in ["bw", "b/n", "bn", "grayscale", "gray"]:
                        out["color_mode"] = "bw"

        # Sinopsis: dc:description, description o summary
        for el in root.iter():
            ln = local_name(el).lower()
            if ln in ("description", "dc:description", "summary") and el.text:
                out["sinopsis"] = limpiar_html_basico(el.text.strip())
                break

        # Categoría: dc:type
        for el in root.iter():
            if local_name(el).lower() in ("type", "dc:type") and el.text:
                out["categoria"] = el.text.strip()
                break

        # Publisher: dc:publisher
        for el in root.iter():
            if local_name(el).lower() in ("publisher", "dc:publisher") and el.text:
                out["publisher"] = el.text.strip()

        # Identificadores: ISBN, ASIN (dc:identifier)
        for el in root.iter():
            if local_name(el).lower() in ("identifier", "dc:identifier") and el.text:
                txt = el.text.strip()
                lower_txt = txt.lower()

                # Limpieza básica
                clean_val = txt
                if lower_txt.startswith("urn:isbn:"):
                    clean_val = txt[9:]
                elif lower_txt.startswith("isbn:"):
                    clean_val = txt[5:]
                elif lower_txt.startswith("urn:uuid:"):
                    # UUID no es ISBN
                    continue

                # Detectar explícitamente si es ISBN
                is_isbn = False
                if "isbn" in lower_txt:
                    is_isbn = True
                else:
                    # Check atributos (scheme, id)
                    for k, v in el.attrib.items():
                        attr_val = v.lower()
                        attr_name = local_name_attr(k).lower()
                        if ("scheme" in attr_name and "isbn" in attr_val) or ("id" in attr_name and "isbn" in attr_val):
                            is_isbn = True
                            break

                # Fallback: si es puramente numérico (o X) de 10/13 dígitos y no tenemos nada
                import re

                candidate = re.sub(r"[^0-9X]", "", clean_val.upper())

                if not is_isbn and len(candidate) in (10, 13) and not out["isbn"]:
                    # Asumimos que podría ser ISBN si no hay otro identifier mejor
                    # Pero es arriesgado sin etiqueta explícita.
                    pass

                if is_isbn:
                    if len(candidate) in (10, 13):
                        # Prioridad: Prefiere ISBN-13
                        current = out.get("isbn")
                        if not current:
                            out["isbn"] = clean_val
                        elif len(re.sub(r"[^0-9X]", "", current)) == 10 and len(candidate) == 13:
                            out["isbn"] = clean_val

        # Fallback: Buscar ISBN en dc:source o dc:relation si aun no tenemos
        if not out["isbn"]:
            for el in root.iter():
                if local_name(el).lower() in ("source", "dc:source", "relation", "dc:relation") and el.text:
                    txt = el.text.strip()
                    lower_txt = txt.lower()
                    if "isbn" in lower_txt:
                        # Extract potential ISBN part
                        # Simple regex for cleaner extraction from strings like "ISBN: 978..."
                        import re

                        match = re.search(
                            r"(?:ISBN(?:\-1[03])?:?\s*)?([0-9X\-]{10,17})",
                            txt,
                            re.IGNORECASE,
                        )
                        if match:
                            candidate_raw = match.group(1)
                            clean_cand = re.sub(r"[^0-9X]", "", candidate_raw.upper())
                            if len(clean_cand) in (10, 13):
                                out["isbn"] = candidate_raw
                                break

        # Roles meta: map id->role
        roles: dict[str, str] = {}
        for el in root.iter():
            if local_name(el).lower() == "meta":
                prop = el.attrib.get("property", "") or el.attrib.get("{http://www.idpf.org/2007/opf}property", "")
                if prop.lower() == "role":
                    ref = el.attrib.get("refines", "") or el.attrib.get("{http://www.idpf.org/2007/opf}refines", "")
                    if ref and el.text:
                        roles[ref.lstrip("#")] = el.text.strip().lower()

        # Asignar roles
        maquet_roles = {"mrk", "dst", "mqt", "mkr"}
        for rid, role in roles.items():
            name = id_to_name.get(rid)
            if not name:
                continue
            if role in maquet_roles:
                out["maquetadores"].append(name)
            elif role in ("trl", "translator"):
                out["traductor"] = name
            elif role in ("ill", "illustrator", "artist"):
                out["ilustrador"] = name
            elif role in ("aut", "author") and not out["autores"]:
                out["autores"].append(name)

        # Heurísticas si falta ilustrador o maquetadores
        if not out["ilustrador"]:
            for c in contributors:
                if any(tok in c.lower() for tok in ("ill", "artist")):
                    out["ilustrador"] = c
                    break
        if not out["maquetadores"]:
            for c in contributors:
                if any(tok in c.lower() for tok in ("saosora", "zeepub")):
                    out["maquetadores"].append(c)
            if not out["maquetadores"]:
                out["maquetadores"].extend(contributors)

        # Dedupe maquetadores
        seen = set()
        mq = []
        for m in out["maquetadores"]:
            if m not in seen:
                seen.add(m)
                mq.append(m)
        out["maquetadores"] = mq

        return out

    try:
        # Abrir EPUB
        if isinstance(data_or_path, (bytes, bytearray)):
            zf = zipfile.ZipFile(io.BytesIO(data_or_path))
        else:
            zf = zipfile.ZipFile(data_or_path)
        opf_data = _read_opf(zf)
        if not opf_data:
            return None
        return _parse_opf(opf_data)
    except Exception:
        return None


def extract_cover_from_epub(data_or_path: bytes | str) -> bytes | None:
    """
    Extrae y devuelve los bytes de la portada embebida en el EPUB,
    buscando primero <meta property="cover"> y luego cualquier
    image/* con 'cover' en id o href. Retorna None si no la halla.
    """
    try:
        if isinstance(data_or_path, (bytes, bytearray)):
            zf = zipfile.ZipFile(io.BytesIO(data_or_path))
        else:
            zf = zipfile.ZipFile(data_or_path)
        namelist = zf.namelist()
        lower_map = {n.lower(): n for n in namelist}

        # 1) localizar OPF
        try:
            container = zf.read("META-INF/container.xml")
            tree = ET.fromstring(container)
            opf_path = next(
                rf.attrib["full-path"]
                for rf in tree.findall(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
                if rf.attrib.get("full-path", "").lower().endswith(".opf")
            )
        except StopIteration:
            opf_path = next(name for name in namelist if name.lower().endswith(".opf"))
        real_opf = lower_map.get(opf_path.lower(), opf_path)

        # 2) leer OPF
        opf_data = zf.read(real_opf)
        root = ET.fromstring(opf_data)
        ns = {"opf": "http://www.idpf.org/2007/opf"}

        # 3) meta cover id
        cover_id = None
        for m in root.findall(".//opf:meta", ns):
            if m.attrib.get("property", "").lower() == "cover":
                cover_id = m.attrib.get("content")
                break

        # 4) manifest lookup
        manifest = root.findall(".//opf:item", ns)
        target_href = None
        if cover_id:
            for item in manifest:
                if item.attrib.get("id") == cover_id:
                    target_href = item.attrib.get("href")
                    break
        if not target_href:
            for item in manifest:
                href = item.attrib.get("href", "").lower()
                iid = item.attrib.get("id", "").lower()
                mt = item.attrib.get("media-type", "")
                if mt.startswith("image/") and "cover" in (iid + href):
                    target_href = item.attrib.get("href")
                    break

        if not target_href:
            return None

        # 5) leer bytes portada
        base = os.path.dirname(real_opf)
        full = f"{base}/{target_href}".lstrip("/")
        real_cover = lower_map.get(full.lower(), full)
        return zf.read(real_cover)
    except Exception:
        return None


async def enrich_metadata_from_epub(
    epub_bytes: bytes | str,
    epub_url: str,
    existing_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Centralized metadata enrichment function.

    Parses OPF metadata, extracts internal title, and extracts filename title from URL.
    Returns a fully populated metadata dictionary.

    Args:
        epub_bytes: EPUB data (bytes or file path)
        epub_url: URL of the EPUB (for extracting filename)
        existing_meta: Optional existing metadata to merge with

    Returns:
        Enriched metadata dictionary
    """
    import logging
    from urllib.parse import unquote, urlparse

    logger = logging.getLogger(__name__)
    meta = existing_meta.copy() if existing_meta else {}

    logger.debug(f"Starting metadata enrichment for URL: {epub_url}")

    try:
        # Parse OPF metadata
        logger.debug("Attempting to parse OPF metadata...")
        opf_meta = await parse_opf_from_epub(epub_bytes)
        if opf_meta:
            logger.debug(
                f"OPF metadata extracted successfully: titulo_volumen={opf_meta.get('titulo_volumen')}, titulo_serie={opf_meta.get('titulo_serie')}"
            )
            # Merge OPF metadata, preserving existing autores if present
            if opf_meta.get("autores"):
                meta["autores"] = opf_meta["autores"]
                meta["autor"] = opf_meta["autores"][0]
                logger.debug(f"Authors found: {meta['autores']}")

            # Merge other OPF fields
            for key in (
                "titulo_serie",
                "titulo_volumen",
                "ilustrador",
                "categoria",
                "publisher",
                "publisher_url",
                "generos",
                "demografia",
                "maquetadores",
                "traductor",
                "sinopsis",
                "epub_version",
                "fecha_modificacion",
                "fecha_publicacion",
                "is_uncensored",
                "color_mode",
                "volume_index",
            ):
                if opf_meta.get(key):
                    meta[key] = opf_meta[key]
        else:
            logger.warning("OPF metadata parsing returned None - no metadata extracted from OPF")
    except Exception as e:
        logger.error(f"enrich_metadata_from_epub: OPF parse failed: {e}", exc_info=True)

    # Extract internal title
    try:
        logger.debug("Attempting to extract internal title...")
        internal_title = extract_internal_title(epub_bytes)
        if internal_title:
            meta["internal_title"] = internal_title
            logger.debug(f"Internal title extracted: {internal_title}")
        else:
            logger.debug("No internal title found in EPUB")
    except Exception as e:
        logger.error(
            f"enrich_metadata_from_epub: internal title extraction failed: {e}",
            exc_info=True,
        )

    # Extract filename title from URL
    try:
        filename_title = unquote(urlparse(epub_url).path.split("/")[-1]).replace(".epub", "")
        meta["filename_title"] = filename_title
        logger.debug(f"Filename title extracted: {filename_title}")
    except Exception as e:
        logger.error(f"enrich_metadata_from_epub: filename extraction failed: {e}", exc_info=True)

    # Extract publisher URL from HTML (prioritized over OPF)
    try:
        html_publisher_url = extract_publisher_url_from_html(epub_bytes)
        if html_publisher_url:
            meta["publisher_url"] = html_publisher_url
            logger.debug(f"enrich_metadata_from_epub: publisher_url updated from HTML: {html_publisher_url}")
    except Exception as e:
        logger.debug(f"enrich_metadata_from_epub: HTML publisher URL extraction failed: {e}")

    logger.info(f"Metadata enrichment completed. Keys present: {list(meta.keys())}")
    return meta


def extract_publisher_url_from_html(data_or_path: bytes | str) -> str | None:
    """
    Busca la URL del publisher/traductor en archivos HTML internos (title/titulo).
    Prioridad:
    1. <p class="salto1"><b>Página Web</b>...<a href="...">
    2. <p class="salto1"><b>Redes sociales</b>...<a href="...">
    """
    try:
        if isinstance(data_or_path, (bytes, bytearray)):
            zf = zipfile.ZipFile(io.BytesIO(data_or_path))
        else:
            zf = zipfile.ZipFile(data_or_path)

        # Buscar archivos candidatos
        candidates = [n for n in zf.namelist() if "title" in n.lower() or "titulo" in n.lower()]

        # Regex patterns
        # Busca el bloque de Página Web
        # <p class="salto1"><b>Página Web</b><br/><a href="...">
        pat_web = re.compile(
            r'<p[^>]*class="salto1"[^>]*>.*?<b>Página Web</b>.*?<a[^>]+href="([^"]+)"',
            re.IGNORECASE | re.DOTALL,
        )

        # Busca el bloque de Redes sociales
        # <p class="salto1"><b>Redes sociales</b><br/><a href="...">
        pat_social = re.compile(
            r'<p[^>]*class="salto1"[^>]*>.*?<b>Redes sociales</b>.*?<a[^>]+href="([^"]+)"',
            re.IGNORECASE | re.DOTALL,
        )

        for name in candidates:
            try:
                content = zf.read(name).decode("utf-8", errors="ignore")

                # 1. Intentar Página Web
                match_web = pat_web.search(content)
                if match_web:
                    return match_web.group(1).strip()

                # 2. Intentar Redes sociales
                match_social = pat_social.search(content)
                if match_social:
                    return match_social.group(1).strip()

            except Exception:
                continue

        return None
    except Exception:
        return None
