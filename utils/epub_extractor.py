import os
import zipfile
import xml.etree.ElementTree as ET
from PIL import Image
import io
import re
import html


def clean_metadata_tags(text):
    """Remove tags like [NL], [NW], [ShinsengumiTL], etc. from metadata"""
    if not text:
        return text
    # Remove all content within square brackets
    cleaned = re.sub(r'\s*\[.*?\]\s*', ' ', text)
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


class EpubMetadataExtractor:
    """
    Extractor de metadatos ligero usando zipfile y ElementTree.
    No requiere dependencias pesadas como ebooklib.
    """

    NAMESPACE = {
        'container': 'urn:oasis:names:tc:opendocument:xmlns:container',
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/',
    }

    def __init__(self, epub_path):
        self.epub_path = epub_path
        self.metadata = {}
        self.cover_data = None
        self.cover_extension = None

    def extract(self):
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as z:
                # 1. Encontrar el archivo OPF
                container_xml = z.read('META-INF/container.xml')
                root = ET.fromstring(container_xml)
                opf_path = root.find('.//container:rootfile', self.NAMESPACE).get('full-path')

                # 2. Leer el OPF
                opf_content = z.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                self.metadata['version'] = opf_root.get('version')

                # 3. Extraer Metadatos Básicos
                metadata_node = opf_root.find('opf:metadata', self.NAMESPACE)
                if metadata_node is not None:
                    # Clean title from tags like [ShinsengumiTL]
                    raw_title = self._get_dc_value(metadata_node, 'title')
                    self.metadata['title'] = clean_metadata_tags(raw_title)
                    self.metadata['publisher'] = self._get_dc_value(metadata_node, 'publisher')
                    self.metadata['language'] = self._get_dc_value(metadata_node, 'language')
                    self.metadata['description'] = self._get_dc_value(metadata_node, 'description')
                    self.metadata['book_type'] = self._get_dc_value(metadata_node, 'type')
                    self.metadata['published_at'] = self._get_dc_value(metadata_node, 'date')

                    # Extraer fecha de modificación de dc:date (específico de EPUB2/Calibre)
                    for date_node in metadata_node.findall('dc:date', self.NAMESPACE):
                        if date_node.get('{http://www.idpf.org/2007/opf}event') == 'modification':
                            self.metadata['modified_at_opf'] = date_node.text
                            break

                    # 3.1 Mapear Roles de Creadores y Contribuidores
                    # Guardamos IDs de creadores para asociar roles refinados
                    creators = {}  # id -> text
                    for node in metadata_node.findall('dc:creator', self.NAMESPACE):
                        creators[node.get('{http://www.w3.org/XML/1998/namespace}id') or node.get('id')] = node.text

                    contributors = {}  # id -> text
                    for node in metadata_node.findall('dc:contributor', self.NAMESPACE):
                        contributors[node.get('{http://www.w3.org/XML/1998/namespace}id') or node.get('id')] = node.text

                    # Roles
                    meta_tags = metadata_node.findall('opf:meta', self.NAMESPACE)
                    role_map = {}  # id -> role (aut, ill, trl, mrk)

                    for meta in meta_tags:
                        refines = meta.get('refines')
                        prop = meta.get('property')
                        if refines and prop == 'role':
                            role_map[refines.replace('#', '')] = meta.text

                    # Asignar personas
                    self.metadata['author'] = self._get_dc_value(metadata_node, 'creator')  # Fallback
                    for cid, text in creators.items():
                        role = role_map.get(cid, "aut")
                        if role == "aut":
                            self.metadata["author"] = text
                        elif role == "ill":
                            self.metadata["illustrator"] = text

                    for cid, text in contributors.items():
                        role = role_map.get(cid)
                        if role == "trl":
                            self.metadata["translator"] = text
                        elif role == "mrk":
                            self.metadata["layout_by"] = text
                        elif role == "ill" and not self.metadata.get("illustrator"):
                            self.metadata["illustrator"] = text

                    # 3.2 Identificadores (ISBN, ASIN, URI)
                    for ident in metadata_node.findall('dc:identifier', self.NAMESPACE):
                        id_text = ident.text or ""
                        lower_id = id_text.lower()
                        if 'isbn:978' in lower_id:  # Prioritize ISBN13
                            self.metadata['isbn'] = id_text.split(':')[-1]
                        elif 'isbn' in lower_id and not self.metadata.get('isbn'):
                            self.metadata['isbn'] = id_text.split(':')[-1]
                        elif 'amazon' in lower_id or 'asin' in lower_id:
                            self.metadata['asin'] = id_text.split(':')[-1]
                        elif 'uri' in lower_id:
                            self.metadata['uri'] = id_text.split('urn:uri:')[-1]

                    # 3.3 Etiquetas (Géneros)
                    tags = []
                    for subject in metadata_node.findall('dc:subject', self.NAMESPACE):
                        if subject.text:
                            tags.append(subject.text)
                    self.metadata['tags'] = tags

                    # 3.4 Series y Volumen (Calibre / EPUB3 metadata)
                    for meta in meta_tags:
                        name = meta.get('name')
                        prop = meta.get('property')

                        if name == 'calibre:series':
                            # Clean series name from tags
                            self.metadata['series'] = clean_metadata_tags(meta.get('content'))
                        elif name == "calibre:series_index":
                            try:
                                self.metadata["volume"] = float(meta.get("content"))
                            except Exception:
                                pass
                        elif prop == 'belongs-to-collection':
                            val = meta.text or metadata_node.find(f'.//opf:meta[@id="{meta.get("id")}"]', self.NAMESPACE).text
                            # Clean series name from tags like [NL], [NW]
                            self.metadata['series'] = clean_metadata_tags(val)
                        elif prop == "group-position" and meta.get("refines") == "#serie":
                            try:
                                self.metadata["volume"] = float(meta.text)
                            except Exception:
                                pass
                        elif prop == 'dcterms:modified':
                            self.metadata['modified_at_opf'] = meta.text

                # 4. Calcular métricas técnicas (palabras, páginas)
                self._calculate_technical_metrics(z, opf_root, os.path.dirname(opf_path))

                # 5. Encontrar la portada
                self._extract_cover(z, opf_root, os.path.dirname(opf_path))

                return self.metadata
        except Exception as e:
            print(f"Error extrayendo metadata de {self.epub_path}: {e}")
            return None

    def _get_dc_value(self, node, tag):
        found = node.find(f'dc:{tag}', self.NAMESPACE)
        return found.text if found is not None else None

    def _calculate_technical_metrics(self, z, opf_root, base_dir):
        """
        Lee el contenido de texto del EPUB para contar palabras y estimar páginas.
        """
        try:
            spine_nodes = opf_root.find('opf:spine', self.NAMESPACE)
            manifest_node = opf_root.find('opf:manifest', self.NAMESPACE)

            if spine_nodes is None or manifest_node is None:
                return

            total_words = 0

            # Mapear itemref idref -> href
            item_map = {}
            for item in manifest_node.findall('opf:item', self.NAMESPACE):
                item_map[item.get('id')] = item.get('href')

            for itemref in spine_nodes.findall('opf:itemref', self.NAMESPACE):
                idref = itemref.get('idref')
                href = item_map.get(idref)

                if href and any(href.lower().endswith(ext) for ext in ['.xhtml', '.html', '.htm', '.xml']):
                    try:
                        full_href = os.path.join(base_dir, href).replace('\\', '/')
                        content = z.read(full_href).decode('utf-8', errors='ignore')

                        # Limpiar HTML básico y contar palabras
                        text = re.sub(r'<[^>]+>', ' ', content)  # Quitar tags
                        text = html.unescape(text)  # Unescape entidades
                        words = len(re.findall(r'\w+', text))
                        total_words += words
                    except Exception:
                        continue

            if total_words > 0:
                self.metadata['word_count'] = total_words
                # Heurística: 300 palabras por página es estándar para libros físicos
                self.metadata['page_count'] = max(1, total_words // 300)
                # Heurística: 200 palabras por minuto es una velocidad de lectura promedio
                self.metadata['reading_time'] = max(1, total_words // 200)
        except Exception:
            pass

    def _extract_cover(self, z, opf_root, base_dir):
        """
        Intenta encontrar la imagen de portada y guardarla en memoria.
        """
        try:
            # Buscar en <meta name="cover" content="id_imagen">
            metadata_node = opf_root.find('opf:metadata', self.NAMESPACE)
            cover_id = None
            for meta in metadata_node.findall('opf:meta', self.NAMESPACE):
                if meta.get('name') == 'cover':
                    cover_id = meta.get('content')
                    break

            manifest_node = opf_root.find('opf:manifest', self.NAMESPACE)
            cover_href = None

            if cover_id:
                # Buscar por ID
                for item in manifest_node.findall('opf:item', self.NAMESPACE):
                    if item.get('id') == cover_id:
                        cover_href = item.get('href')
                        break

            if not cover_href:
                # 3. EPUB3 Fallback: Buscar en el manifest un item con properties="cover-image"
                for item in manifest_node.findall('opf:item', self.NAMESPACE):
                    if item.get('properties') == 'cover-image':
                        cover_href = item.get('href')
                        break

            if not cover_href:
                # 4. Fallback: buscar archivos que tengan "cover" en el nombre o id
                for item in manifest_node.findall('opf:item', self.NAMESPACE):
                    item_id = item.get('id', '').lower()
                    href = item.get('href', '').lower()
                    if 'cover' in item_id or 'cover' in href:
                        if any(href.endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                            cover_href = item.get('href')
                            break

            if cover_href:
                full_href = os.path.join(base_dir, cover_href).replace('\\', '/')
                self.cover_data = z.read(full_href)
                self.cover_extension = os.path.splitext(cover_href)[1]
        except Exception:
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
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 1. VERSION ORIGINAL (sin modificar, full quality)
                original_path = output_path.replace('.jpg', '_original.jpg')
                img.save(original_path, "JPEG", quality=95, optimize=True)
                
                # 2. VERSION HIGH (800px, quality 85)
                high_path = output_path.replace('.jpg', '_high.jpg')
                high_img = img.copy()
                if high_img.width > 800:
                    ratio = 800 / float(high_img.width)
                    height = int((float(high_img.height) * float(ratio)))
                    high_img = high_img.resize((800, height), Image.LANCZOS)
                high_img.save(high_path, "JPEG", quality=85, optimize=True)
                
                # 3. VERSION MEDIUM (400px, quality 80)
                medium_path = output_path.replace('.jpg', '_medium.jpg')
                medium_img = img.copy()
                if medium_img.width > 400:
                    ratio = 400 / float(medium_img.width)
                    height = int((float(medium_img.height) * float(ratio)))
                    medium_img = medium_img.resize((400, height), Image.LANCZOS)
                medium_img.save(medium_path, "JPEG", quality=80, optimize=True)
                
                # 4. VERSION LOW (200px, quality 70) - DEFAULT PARA UI
                low_path = output_path.replace('.jpg', '_low.jpg')
                low_img = img.copy()
                if low_img.width > 200:
                    ratio = 200 / float(low_img.width)
                    height = int((float(low_img.height) * float(ratio)))
                    low_img = low_img.resize((200, height), Image.LANCZOS)
                low_img.save(low_path, "JPEG", quality=70, optimize=True, progressive=True)
                
                return {
                    'original': original_path,
                    'high': high_path,
                    'medium': medium_path,
                    'low': low_path
                }
            except Exception as e:
                print(f"Error guardando portada: {e}")
        return None
