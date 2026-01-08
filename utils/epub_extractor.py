import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from PIL import Image
import io

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
                
                # 3. Extraer Metadatos Básicos
                metadata_node = opf_root.find('opf:metadata', self.NAMESPACE)
                if metadata_node is not None:
                    self.metadata['title'] = self._get_dc_value(metadata_node, 'title')
                    self.metadata['publisher'] = self._get_dc_value(metadata_node, 'publisher')
                    self.metadata['language'] = self._get_dc_value(metadata_node, 'language')
                    self.metadata['description'] = self._get_dc_value(metadata_node, 'description')
                    self.metadata['book_type'] = self._get_dc_value(metadata_node, 'type')
                    self.metadata['published_at'] = self._get_dc_value(metadata_node, 'date')
                    
                    # 3.1 Mapear Roles de Creadores y Contribuidores
                    # Guardamos IDs de creadores para asociar roles refinados
                    creators = {} # id -> text
                    for node in metadata_node.findall('dc:creator', self.NAMESPACE):
                        creators[node.get('{http://www.w3.org/XML/1998/namespace}id') or node.get('id')] = node.text
                    
                    contributors = {} # id -> text
                    for node in metadata_node.findall('dc:contributor', self.NAMESPACE):
                        contributors[node.get('{http://www.w3.org/XML/1998/namespace}id') or node.get('id')] = node.text
                    
                    # Roles
                    meta_tags = metadata_node.findall('opf:meta', self.NAMESPACE)
                    role_map = {} # id -> role (aut, ill, trl, mrk)
                    
                    for meta in meta_tags:
                        refines = meta.get('refines')
                        prop = meta.get('property')
                        if refines and prop == 'role':
                            role_map[refines.replace('#', '')] = meta.text

                    # Asignar personas
                    self.metadata['author'] = self._get_dc_value(metadata_node, 'creator') # Fallback
                    for cid, text in creators.items():
                        role = role_map.get(cid, 'aut')
                        if role == 'aut': self.metadata['author'] = text
                        elif role == 'ill': self.metadata['illustrator'] = text
                    
                    for cid, text in contributors.items():
                        role = role_map.get(cid)
                        if role == 'trl': self.metadata['translator'] = text
                        elif role == 'mrk': self.metadata['layout_by'] = text
                        elif role == 'ill' and not self.metadata.get('illustrator'):
                            self.metadata['illustrator'] = text

                    # 3.2 Identificadores (ISBN, ASIN, URI)
                    for ident in metadata_node.findall('dc:identifier', self.NAMESPACE):
                        id_text = ident.text or ""
                        lower_id = id_text.lower()
                        if 'isbn:978' in lower_id: # Prioritize ISBN13
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
                            self.metadata['series'] = meta.get('content')
                        elif name == 'calibre:series_index':
                            try: self.metadata['volume'] = float(meta.get('content'))
                            except: pass
                        elif prop == 'belongs-to-collection':
                            val = meta.text or metadata_node.find(f'.//opf:meta[@id="{meta.get("id")}"]', self.NAMESPACE).text
                            self.metadata['series'] = val
                        elif prop == 'group-position' and meta.get('refines') == '#serie':
                            try: self.metadata['volume'] = float(meta.text)
                            except: pass
                        elif prop == 'dcterms:modified':
                            self.metadata['modified_at_opf'] = meta.text

                # 4. Encontrar la portada
                self._extract_cover(z, opf_root, os.path.dirname(opf_path))
                
                return self.metadata
        except Exception as e:
            print(f"Error extrayendo metadata de {self.epub_path}: {e}")
            return None

    def _get_dc_value(self, node, tag):
        found = node.find(f'dc:{tag}', self.NAMESPACE)
        return found.text if found is not None else None

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
                # Fallback: buscar archivos que tengan "cover" en el nombre o id
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
        except:
            pass

    def save_cover(self, output_path):
        """
        Guarda la portada extraída en el disco (opcionalmente redimensionándola).
        """
        if self.cover_data and self.cover_extension:
            try:
                img = Image.open(io.BytesIO(self.cover_data))
                # Convertir a RGB si es necesario (para JPEG)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionar para ahorrar espacio si es muy grande
                if img.width > 600:
                    ratio = 600 / float(img.width)
                    height = int((float(img.height) * float(ratio)))
                    img = img.resize((600, height), Image.LANCZOS)
                
                img.save(output_path, "JPEG", quality=85)
                return True
            except Exception as e:
                print(f"Error guardando portada: {e}")
        return False
