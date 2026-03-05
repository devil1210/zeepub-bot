import html
import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image


def clean_metadata_tags(text):
    """Remove tags like [NL], [NW], [ShinsengumiTL], etc. from metadata"""
    if not text:
        return text
    # Remove all content within square brackets
    cleaned = re.sub(r"\s*\[.*?\]\s*", " ", text)
    # Remove multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


class EpubMetadataExtractor:
    """
    Extractor de metadatos ligero usando zipfile y ElementTree.
    No requiere dependencias pesadas como ebooklib.
    """

    NAMESPACE = {
        "container": "urn:oasis:names:tc:opendocument:xmlns:container",
        "opf": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    def __init__(self, epub_path):
        self.epub_path = epub_path
        self.metadata = {}
        self.cover_data = None
        self.cover_extension = None

    def extract(self):
        try:
            with zipfile.ZipFile(self.epub_path, "r") as z:
                # 1. Encontrar el archivo OPF
                container_xml = z.read("META-INF/container.xml")
                root = ET.fromstring(container_xml)
                opf_path = root.find(".//container:rootfile", self.NAMESPACE).get("full-path")

                # 2. Leer el OPF
                opf_content = z.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                self.metadata["version"] = opf_root.get("version")

                # 3. Extraer Metadatos Básicos
                metadata_node = opf_root.find("opf:metadata", self.NAMESPACE)
                if metadata_node is not None:
                    # Clean title from tags like [ShinsengumiTL]
                    raw_title = self._get_dc_value(metadata_node, "title")
                    self.metadata["title"] = raw_title
                    self.metadata["publisher"] = self._get_dc_value(metadata_node, "publisher")
                    self.metadata["language"] = self._get_dc_value(metadata_node, "language")
                    self.metadata["description"] = self._get_dc_value(metadata_node, "description")
                    self.metadata["book_type"] = self._get_dc_value(metadata_node, "type")
                    self.metadata["published_at"] = self._get_dc_value(metadata_node, "date")

                    # Extraer fecha de modificación de dc:date (específico de EPUB2/Calibre)
                    for date_node in metadata_node.findall("dc:date", self.NAMESPACE):
                        if date_node.get("{http://www.idpf.org/2007/opf}event") == "modification":
                            self.metadata["modified_at_opf"] = date_node.text
                            break

                    # 3.1 Mapear Roles de Creadores y Contribuidores
                    creators = {}  # id -> text
                    contributors = {}  # id -> text
                    creators_jap = {}  # id -> jap_text
                    role_map = {}  # id -> role (aut, ill, trl, mrk)

                    def get_attr_agnostic(node, attr_name):
                        """Obtiene un atributo sin importar si tiene namespace."""
                        if node is None:
                            return None
                        for k, v in node.attrib.items():
                            if k == attr_name or k.endswith("}" + attr_name):
                                return v
                        return None

                    # Extraer toda la info de los meta tags en una sola pasada
                    meta_tags = []
                    for child in metadata_node:
                        tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag

                        if tag_name == "creator":
                            cid = get_attr_agnostic(child, "id")
                            if cid:
                                creators[cid] = child.text
                        elif tag_name == "contributor":
                            cid = get_attr_agnostic(child, "id")
                            if cid:
                                contributors[cid] = child.text
                        elif tag_name == "meta":
                            meta_tags.append(child)
                            refines = get_attr_agnostic(child, "refines")
                            # EPUB3 uses 'property', EPUB2 uses 'name'
                            prop = get_attr_agnostic(child, "property") or get_attr_agnostic(child, "name")

                            if refines:
                                cid = refines.replace("#", "")
                                if prop == "role":
                                    role_map[cid] = child.text
                                elif prop == "alternate-script" and (
                                    get_attr_agnostic(child, "lang") in ("ja", "ja-JP")
                                    or child.get("{http://www.w3.org/XML/1998/namespace}lang") in ("ja", "ja-JP")
                                ):
                                    creators_jap[cid] = child.text

                    # Asignar personas
                    self.metadata["author"] = self._get_dc_value(metadata_node, "creator")  # Fallback
                    self.metadata["author_jap"] = None
                    self.metadata["illustrator"] = None
                    self.metadata["illustrator_jap"] = None

                    for cid, text in creators.items():
                        role = role_map.get(cid, "aut")
                        jap_name = creators_jap.get(cid)

                        if role == "aut":
                            self.metadata["author"] = text
                            self.metadata["author_jap"] = jap_name
                        elif role == "ill":
                            self.metadata["illustrator"] = text
                            self.metadata["illustrator_jap"] = jap_name

                    for cid, text in contributors.items():
                        role = role_map.get(cid)
                        jap_name = creators_jap.get(cid)
                        if role == "trl":
                            self.metadata["translator"] = text
                        elif role == "mrk":
                            self.metadata["layout_by"] = text
                        elif role == "ill":
                            if not self.metadata.get("illustrator"):
                                self.metadata["illustrator"] = text
                            if not self.metadata.get("illustrator_jap"):
                                self.metadata["illustrator_jap"] = jap_name

                    # 3.2 Identificadores (ISBN, ASIN, URI)
                    for ident in metadata_node.findall("dc:identifier", self.NAMESPACE):
                        id_text = ident.text or ""
                        clean_id = re.sub(
                            r"^urn:(isbn|amazon|uri|uuid|asin):",
                            "",
                            id_text,
                            flags=re.IGNORECASE,
                        ).strip()

                        lower_id = id_text.lower()
                        if "isbn" in lower_id:
                            if (not self.metadata.get("isbn")) or ("978" in clean_id):
                                self.metadata["isbn"] = clean_id
                        elif "amazon" in lower_id or "asin" in lower_id:
                            self.metadata["asin"] = clean_id
                        elif "uri" in lower_id:
                            self.metadata["uri"] = clean_id

                    # 3.3 Etiquetas (Géneros)
                    tags = []
                    for subject in metadata_node.findall("dc:subject", self.NAMESPACE):
                        if subject.text:
                            tags.append(subject.text)
                    self.metadata["tags"] = tags

                    # 3.4 Series y Volumen (EPUB3 / Calibre)
                    collection_ids = {}

                    # PASADA 1: Buscar en belongs-to-collection (EPUB3)
                    for meta in meta_tags:
                        prop = get_attr_agnostic(meta, "property")
                        meta_id = get_attr_agnostic(meta, "id")
                        if prop == "belongs-to-collection":
                            val = (meta.text or "").strip()
                            if val:
                                self.metadata["series"] = clean_metadata_tags(val)
                                if meta_id:
                                    collection_ids[meta_id] = self.metadata["series"]

                    # PASADA 2: Buscar en calibre:series o simplemente 'series'
                    if not self.metadata.get("series"):
                        for meta in meta_tags:
                            name = get_attr_agnostic(meta, "name")
                            prop = get_attr_agnostic(meta, "property")
                            content = get_attr_agnostic(meta, "content")

                            # Intentar varios nombres comunes de series
                            potential_props = ["calibre:series", "series", "collection", "belongs-to-collection"]
                            if name in potential_props or prop in potential_props:
                                val = content or meta.text
                                if val:
                                    self.metadata["series"] = clean_metadata_tags(val)
                                    break

                    # PASADA 3: Volumen / Indice
                    for meta in meta_tags:
                        name = get_attr_agnostic(meta, "name")
                        prop = get_attr_agnostic(meta, "property")
                        content = get_attr_agnostic(meta, "content")

                        # Indices de volumen
                        if name in ("calibre:series_index", "series_index") or prop in (
                            "calibre:series_index",
                            "series_index",
                        ):
                            if not self.metadata.get("volume"):
                                try:
                                    self.metadata["volume"] = float(content or meta.text)
                                except (ValueError, TypeError, Exception):
                                    pass

                        elif prop == "group-position":
                            ref = (get_attr_agnostic(meta, "refines") or "").replace("#", "")
                            if ref == "serie" or ref in collection_ids:
                                try:
                                    self.metadata["volume"] = float(meta.text)
                                except (ValueError, TypeError, Exception):
                                    pass
                        elif prop == "dcterms:modified":
                            self.metadata["modified_at_opf"] = meta.text

                    # 3.4.1 Detección automática de características de edición
                    all_tags_text = " ".join(tags).lower()

                    # Defaults
                    self.metadata["is_uncensored"] = 0
                    self.metadata["color_mode"] = "bw"
                    self.metadata["edition"] = None

                    # EPUB3 schema:bookEdition property
                    for meta in meta_tags:
                        if meta.get("property") == "schema:bookEdition":
                            self.metadata["edition"] = meta.text.strip()
                            break

                    # Option 1: Detection via tags/subjects
                    if any(x in all_tags_text for x in ["sin censura", "uncensored", "no censura"]):
                        self.metadata["is_uncensored"] = 1

                    # Also check in edition field if found
                    edition_text = (self.metadata.get("edition") or "").lower()
                    if any(x in edition_text for x in ["sin censura", "uncensored", "no censura"]):
                        self.metadata["is_uncensored"] = 1

                    if (
                        any(x in all_tags_text for x in ["ilustraciones a color", "color", "full color"])
                        or "color" in edition_text
                    ):
                        self.metadata["color_mode"] = "color"
                    elif any(x in all_tags_text for x in ["blanco y negro", "b&w", "grayscale", "b/n"]):
                        self.metadata["color_mode"] = "bw"

                    # Option 3: Detection via custom meta properties (Zeepub extensions)
                    for meta in meta_tags:
                        name = meta.get("name")
                        prop = meta.get("property")
                        content = meta.get("content")

                        # Uncensored check
                        if name == "zeepub:uncensored" or prop == "zeepub:uncensored":
                            val = (content or meta.text or "").lower().strip()
                            if val in ["true", "1", "yes"]:
                                self.metadata["is_uncensored"] = 1
                            elif val in ["false", "0", "no"]:
                                self.metadata["is_uncensored"] = 0

                        # Color mode check
                        if name == "zeepub:color_mode" or prop == "zeepub:color_mode":
                            val = (content or meta.text or "").lower().strip()
                            if val in ["color", "full-color", "c"]:
                                self.metadata["color_mode"] = "color"
                            elif val in ["bw", "b/n", "bn", "grayscale", "gray"]:
                                self.metadata["color_mode"] = "bw"

                    if not self.metadata.get("title"):
                        self.metadata["title"] = clean_metadata_tags(raw_title)

                # 4. Calcular métricas técnicas (palabras, páginas)
                self._calculate_technical_metrics(z, opf_root, os.path.dirname(opf_path))

                # 5. Encontrar la portada
                self._extract_cover(z, opf_root, os.path.dirname(opf_path))

                return self.metadata
        except Exception as e:
            print(f"Error extrayendo metadata de {self.epub_path}: {e}")
            return None

    def _get_dc_value(self, node, tag):
        found = node.find(f"dc:{tag}", self.NAMESPACE)
        return found.text if found is not None else None

    def _calculate_technical_metrics(self, z, opf_root, base_dir):
        """
        Lee el contenido de texto del EPUB para contar palabras y estimar páginas.
        """
        try:
            spine_nodes = opf_root.find("opf:spine", self.NAMESPACE)
            manifest_node = opf_root.find("opf:manifest", self.NAMESPACE)

            if spine_nodes is None or manifest_node is None:
                return

            total_words = 0

            # Mapear itemref idref -> href
            item_map = {}
            for item in manifest_node.findall("opf:item", self.NAMESPACE):
                item_map[item.get("id")] = item.get("href")

            for itemref in spine_nodes.findall("opf:itemref", self.NAMESPACE):
                idref = itemref.get("idref")
                href = item_map.get(idref)

                if href and any(href.lower().endswith(ext) for ext in [".xhtml", ".html", ".htm", ".xml", ".txt"]):
                    try:
                        raw_path = os.path.join(base_dir, href)
                        full_href = os.path.normpath(raw_path).replace("\\", "/")
                        if full_href.startswith("/"):
                            full_href = full_href[1:]

                        content = z.read(full_href).decode("utf-8", errors="ignore")

                        # Limpiar HTML básico y contar palabras
                        text = re.sub(r"<[^>]+>", " ", content)  # Quitar tags
                        text = html.unescape(text)  # Unescape entidades
                        words = len(re.findall(r"\w+", text))
                        total_words += words
                    except Exception:
                        continue

            if total_words > 0:
                self.metadata["word_count"] = total_words
                # Heurística: 300 palabras por página es estándar para libros físicos
                self.metadata["page_count"] = max(1, total_words // 300)
                # Heurística: 200 palabras por minuto es una velocidad de lectura promedio
                self.metadata["reading_time"] = max(1, total_words // 200)
        except Exception:
            pass

    def _extract_cover(self, z, opf_root, base_dir):
        """
        Intenta encontrar la imagen de portada y guardarla en memoria.
        """
        try:
            metadata_node = opf_root.find("opf:metadata", self.NAMESPACE)
            cover_id = None

            # 1. Buscar en <meta name="cover" content="id_imagen">
            # Pasada robusta sobre todos los hijos
            for child in metadata_node:
                tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag_name == "meta":
                    if child.get("name") == "cover":
                        cover_id = child.get("content")
                        break

            manifest_node = opf_root.find("opf:manifest", self.NAMESPACE)
            cover_href = None

            # 2. Buscar por ID (EPUB2)
            if cover_id:
                for item in manifest_node.findall("opf:item", self.NAMESPACE):
                    if item.get("id") == cover_id:
                        cover_href = item.get("href")
                        break

            # 3. EPUB3 Fallback: Buscar en el manifest un item con properties="cover-image"
            if not cover_href:
                for item in manifest_node.findall("opf:item", self.NAMESPACE):
                    # properties puede contener múltiples valores separados por espacio
                    properties = item.get("properties", "").split()
                    if "cover-image" in properties:
                        cover_href = item.get("href")
                        break

            # 4. Fallback extremo: buscar archivos que tengan "cover" en el nombre o id
            if not cover_href:
                for item in manifest_node.findall("opf:item", self.NAMESPACE):
                    item_id = item.get("id", "").lower()
                    href = item.get("href", "").lower()
                    if "cover" in item_id or "cover" in href:
                        if any(href.endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                            cover_href = item.get("href")
                            break

            if cover_href:
                # IMPORTANTE: Normalizar ruta para resolver '..' y usar separadores correctos
                # ZipFile no resuelve '..' automáticamente.
                raw_path = os.path.join(base_dir, cover_href)
                full_href = os.path.normpath(raw_path).replace("\\", "/")

                # Asegurarse de que no empiece por '/' (algunas veces normpath lo hace si base_dir es vacío)
                if full_href.startswith("/"):
                    full_href = full_href[1:]

                self.cover_data = z.read(full_href)
                self.cover_extension = os.path.splitext(cover_href)[1]
        except Exception:
            # Silencioso pero útil para debug manual si es necesario
            pass

    def save_cover(self, output_path):
        """
        Guarda la portada extraída en el disco en 4 versiones progresivas:
        1. Original: Sin modificar (full quality)
        2. High: 800px, quality 85%
        3. Medium: 400px, quality 80%
        4. Low: 200px, quality 70% (default para UI - carga ultra rápida)

        Returns dict with paths for all versions
        """
        if self.cover_data and self.cover_extension:
            try:
                img = Image.open(io.BytesIO(self.cover_data))
                # Convertir a RGB si es necesario (para JPEG)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # 1. VERSION ORIGINAL (sin modificar, full quality)
                original_path = output_path.replace(".jpg", "_original.jpg")
                img.save(original_path, "JPEG", quality=95, optimize=True)

                # 2. VERSION HIGH (800px, quality 85)
                high_path = output_path.replace(".jpg", "_high.jpg")
                high_img = img.copy()
                if high_img.width > 800:
                    ratio = 800 / float(high_img.width)
                    height = int(float(high_img.height) * float(ratio))
                    high_img = high_img.resize((800, height), Image.LANCZOS)
                high_img.save(high_path, "JPEG", quality=85, optimize=True)

                # 3. VERSION MEDIUM (400px, quality 80)
                medium_path = output_path.replace(".jpg", "_medium.jpg")
                medium_img = img.copy()
                if medium_img.width > 400:
                    ratio = 400 / float(medium_img.width)
                    height = int(float(medium_img.height) * float(ratio))
                    medium_img = medium_img.resize((400, height), Image.LANCZOS)
                medium_img.save(medium_path, "JPEG", quality=80, optimize=True)

                # 4. VERSION LOW (200px, quality 70) - DEFAULT PARA UI
                low_path = output_path.replace(".jpg", "_low.jpg")
                low_img = img.copy()
                if low_img.width > 200:
                    ratio = 200 / float(low_img.width)
                    height = int(float(low_img.height) * float(ratio))
                    low_img = low_img.resize((200, height), Image.LANCZOS)
                low_img.save(low_path, "JPEG", quality=70, optimize=True, progressive=True)

                return {
                    "original": original_path,
                    "high": high_path,
                    "medium": medium_path,
                    "low": low_path,
                }
            except Exception as e:
                print(f"Error guardando portada: {e}")
        return None
