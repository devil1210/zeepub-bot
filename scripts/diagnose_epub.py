"""
Script para diagnosticar problemas con archivos EPUB
"""

import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def diagnose_epub(epub_path):
    """Diagnostica un archivo EPUB y muestra información detallada."""

    print(f"🔍 DIAGNÓSTICO DE EPUB: {epub_path}")
    print("=" * 60)

    # Verificar que el archivo exista
    path = Path(epub_path)
    if not path.exists():
        print(f"❌ ERROR: El archivo no existe: {epub_path}")
        return False

    # Verificar tamaño
    file_size = path.stat().st_size
    print(f"📊 Tamaño: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")

    if file_size == 0:
        print("❌ ERROR: El archivo está vacío")
        return False

    # Intentar abrir como ZIP
    try:
        with zipfile.ZipFile(path, "r") as zip_file:
            print("✅ Formato ZIP válido")

            # Listar archivos
            file_list = zip_file.namelist()
            print(f"📋 Total de archivos: {len(file_list)}")

            # Buscar archivos importantes
            opf_files = [f for f in file_list if f.lower().endswith(".opf")]
            container_files = [f for f in file_list if "container.xml" in f.lower()]
            ncx_files = [f for f in file_list if f.lower().endswith(".ncx")]
            html_files = [
                f for f in file_list if f.lower().endswith((".html", ".htm", ".xhtml"))
            ]

            print("\n📁 ARCHIVOS ENCONTRADOS:")
            print(f"   📄 OPF (metadata): {len(opf_files)}")
            for opf in opf_files:
                print(f"      - {opf}")

            print(f"   📦 Container.xml: {len(container_files)}")
            for container in container_files:
                print(f"      - {container}")

            print(f"   📑 NCX (tabla de contenidos): {len(ncx_files)}")
            for ncx in ncx_files[:3]:  # Mostrar solo los primeros 3
                print(f"      - {ncx}")
            if len(ncx_files) > 3:
                print(f"      ... y {len(ncx_files) - 3} más")

            print(f"   📄 HTML/XHTML: {len(html_files)} archivos")

            # Analizar container.xml si existe
            if container_files:
                print("\n🔍 ANALIZANDO CONTAINER.XML:")
                try:
                    container_content = zip_file.read(container_files[0])
                    root = ET.fromstring(container_content)

                    # Buscar rootfile
                    namespaces = {
                        "container": "urn:oasis:names:tc:opendocument:xmlns:container"
                    }
                    rootfiles = root.findall(".//container:rootfile", namespaces)

                    for rootfile in rootfiles:
                        opf_path = rootfile.get("full-path", "")
                        print(f"   📖 Apunta a OPF: {opf_path}")

                        # Verificar que el OPF exista
                        if opf_path in file_list:
                            print("   ✅ OPF encontrado en el ZIP")
                        else:
                            print("   ❌ OPF NO encontrado en el ZIP")

                except Exception as e:
                    print(f"   ❌ Error leyendo container.xml: {e}")

            # Analizar OPF si existe
            if opf_files:
                print("\n🔍 ANALIZANDO OPF:")
                try:
                    opf_content = zip_file.read(opf_files[0])
                    root = ET.fromstring(opf_content)

                    # Namespaces comunes
                    namespaces = {
                        "opf": "http://www.idpf.org/2007/opf",
                        "dc": "http://purl.org/dc/elements/1.1/",
                    }

                    # Extraer metadata básica
                    title_elem = root.find(".//dc:title", namespaces)
                    author_elem = root.find(".//dc:creator", namespaces)
                    lang_elem = root.find(".//dc:language", namespaces)

                    print(
                        f"   📖 Título: {title_elem.text if title_elem is not None else 'No encontrado'}"
                    )
                    print(
                        f"   ✍️ Autor: {author_elem.text if author_elem is not None else 'No encontrado'}"
                    )
                    print(
                        f"   🌐 Idioma: {lang_elem.text if lang_elem is not None else 'No encontrado'}"
                    )

                    # Contar metadatos
                    metadata_items = root.findall(".//dc:*", namespaces)
                    print(f"   📊 Metadatos DC: {len(metadata_items)} encontrados")

                except Exception as e:
                    print(f"   ❌ Error leyendo OPF: {e}")

            print("\n✅ DIAGNÓSTICO COMPLETADO")
            return True

    except zipfile.BadZipFile:
        print("❌ ERROR: El archivo no es un ZIP válido (no es un EPUB)")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Uso: python diagnose_epub.py <ruta_al_epub>")
        print("Ejemplo: python diagnose_epub.py /path/to/book.epub")
        return

    epub_path = sys.argv[1]
    diagnose_epub(epub_path)


if __name__ == "__main__":
    main()
