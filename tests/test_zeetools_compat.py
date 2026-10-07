# tests/test_zeetools_compat.py
import asyncio
import io
import sys
import zipfile

sys.path.insert(0, ".")
from services.epub_service import parse_opf_from_epub
from utils.epub_extractor import EpubMetadataExtractor
from utils.metadata_utils import process_book_identity_comprehensive

OPF_ZEETOOLS_SERIES = """<?xml version="1.0" encoding="utf-8"?>
<package version="3.0" unique-identifier="BookId" xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <metadata>
    <dc:identifier id="BookId">urn:uuid:01924b89-9132-73a4-9419-f53e20e6a8d0</dc:identifier>
    <dc:title id="title" xml:lang="en">The Eminence in Shadow, Vol. 5</dc:title>
    <meta refines="#title" property="title-type">main</meta>
    <meta refines="#title" property="alternate-script" xml:lang="es">Eminencia en las Sombras, Vol. 5</meta>
    <meta refines="#title" property="alternate-script" xml:lang="ja-Latn">Kage no Jitsuryokusha ni Naritakute! Vol. 5</meta>
    <dc:language>es</dc:language>
    <dc:creator id="creator01">Daisuke Aizawa</dc:creator>
    <meta refines="#creator01" property="role" scheme="marc:relators">aut</meta>
    <dc:description>En la &lt;Familia Hestia&gt; todo marcha bien.&lt;br/&gt;Segundo párrafo con &lt;b&gt;negrita&lt;/b&gt;.</dc:description>
    <dc:identifier id="isbn13">urn:isbn:978-4-04-107000-0</dc:identifier>
    <meta refines="#isbn13" property="identifier-type" scheme="onix:codelist5">15</meta>
    <dc:identifier id="amazon-id">urn:amazon:B0BXYZ1234</dc:identifier>
    <dc:contributor id="contrib01">Zack</dc:contributor>
    <meta refines="#contrib01" property="role" scheme="marc:relators">edt</meta>
    <dc:identifier id="uri-id">https://fansub.org</dc:identifier>
    <meta refines="#uri-id" property="identifier-type">uri</meta>
    <meta id="serie" property="belongs-to-collection" xml:lang="en">The Eminence in Shadow [NL]</meta>
    <meta refines="#serie" property="collection-type">series</meta>
    <meta refines="#serie" property="group-position">5</meta>
    <meta refines="#serie" property="alternate-script" xml:lang="es">Eminencia en las Sombras</meta>
    <meta refines="#serie" property="alternate-script" xml:lang="ja-Latn">Kage no Jitsuryokusha ni Naritakute!</meta>
  </metadata>
  <manifest>
    <item id="c" href="cover.jpg" media-type="image/jpeg"/>
    <item id="text1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="text1"/>
  </spine>
</package>"""

OPF_ZEETOOLS_STANDALONE = """<?xml version="1.0" encoding="utf-8"?>
<package version="3.0" unique-identifier="BookId" xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <metadata>
    <dc:identifier id="BookId">urn:uuid:01924b99-1234-73a4-9419-f53e20e6a8d0</dc:identifier>
    <dc:title id="title" xml:lang="en">I Want to Eat Your Pancreas</dc:title>
    <meta refines="#title" property="title-type">main</meta>
    <meta refines="#title" property="alternate-script" xml:lang="es">Quiero Comerme tu Páncreas</meta>
    <dc:language>es</dc:language>
    <dc:creator id="creator01">Yoru Sumino</dc:creator>
    <meta refines="#creator01" property="role" scheme="marc:relators">aut</meta>
    <dc:description>Una novela única sobre la vida y el tiempo.</dc:description>
  </metadata>
  <manifest>
    <item id="c" href="cover.jpg" media-type="image/jpeg"/>
    <item id="text1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="text1"/>
  </spine>
</package>"""

OPF_CALIBRE_LEGACY = """<?xml version="1.0" encoding="utf-8"?>
<package version="2.0" unique-identifier="BookId" xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <metadata>
    <dc:title>Overlord 01 - El Rey No-Muerto</dc:title>
    <dc:creator>Kugane Maruyama</dc:creator>
    <meta name="calibre:series" content="Overlord"/>
    <meta name="calibre:series_index" content="1"/>
  </metadata>
  <manifest>
    <item id="text1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="text1"/>
  </spine>
</package>"""


def build_epub(opf_content: str, path: str = "EPUB/package.opf") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "META-INF/container.xml",
            f"""<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles><rootfile full-path="{path}" media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
        )
        z.writestr(path, opf_content)
        z.writestr("EPUB/ch1.xhtml", "<html><body><p>Hola mundo</p></body></html>")
    return buf.getvalue()


async def test_all():
    # 1. Test ZeeTools con Serie (epub_service)
    epub_bytes_a = build_epub(OPF_ZEETOOLS_SERIES)
    m_a = await parse_opf_from_epub(epub_bytes_a)
    print("Test A (epub_service):")
    print("  titulo_volumen:", m_a["titulo_volumen"])
    print("  spanish_title:", m_a["spanish_title"])
    print("  titulo_serie:", m_a["titulo_serie"])
    print("  series_spanish:", m_a["series_spanish"])
    print("  volume_index:", m_a["volume_index"])
    print("  uuid:", m_a["uuid"])
    print("  asin:", m_a["asin"])
    print("  editor:", m_a["editor"])
    print("  publisher_url:", m_a["publisher_url"])
    print("  sinopsis:", repr(m_a["sinopsis"]))
    assert m_a["spanish_title"] == "Eminencia en las Sombras, Vol. 5"
    assert m_a["series_spanish"] == "Eminencia en las Sombras"
    assert m_a["series_english"] == "The Eminence in Shadow"
    assert m_a["categoria"] == "Novela ligera"
    assert m_a["volume_index"] == 5.0
    assert m_a["uuid"] == "01924b89-9132-73a4-9419-f53e20e6a8d0"
    assert m_a["asin"] == "B0BXYZ1234"
    assert m_a["editor"] == "Zack"
    assert m_a["publisher_url"] == "https://fansub.org"
    assert "<Familia Hestia>" in m_a["sinopsis"]
    assert "<b>" not in m_a["sinopsis"]
    print("-> Test A PASADO OK!\n")

    # 2. Test ZeeTools Standalone (Novela Única)
    epub_bytes_b = build_epub(OPF_ZEETOOLS_STANDALONE)
    m_b = await parse_opf_from_epub(epub_bytes_b)
    print("Test B (epub_service standalone):")
    print("  titulo_volumen:", m_b["titulo_volumen"])
    print("  spanish_title:", m_b["spanish_title"])
    print("  titulo_serie:", m_b["titulo_serie"])
    print("  is_standalone:", m_b["is_standalone"])
    print("  volume_index:", m_b["volume_index"])
    assert m_b["is_standalone"] is True
    assert m_b["titulo_serie"] == "Quiero Comerme tu Páncreas"
    assert m_b["titulo_serie"] != "Unknown"
    print("-> Test B PASADO OK!\n")

    # 3. Test Calibre Legacy (Retrocompatibilidad)
    epub_bytes_c = build_epub(OPF_CALIBRE_LEGACY)
    m_c = await parse_opf_from_epub(epub_bytes_c)
    print("Test C (epub_service calibre legacy):")
    print("  titulo_serie:", m_c["titulo_serie"])
    print("  volume_index:", m_c["volume_index"])
    assert m_c["titulo_serie"] == "Overlord"
    assert m_c["volume_index"] == 1.0
    print("-> Test C PASADO OK!\n")

    # 4. Test EpubMetadataExtractor con archivo físico
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
        tmp.write(epub_bytes_a)
        tmp_path = tmp.name

    try:
        extractor = EpubMetadataExtractor(tmp_path)
        meta_ext = extractor.extract()
        print("Test D (EpubMetadataExtractor):")
        print("  title:", meta_ext.get("title"))
        print("  spanish_title:", meta_ext.get("spanish_title"))
        print("  series:", meta_ext.get("series"))
        print("  series_spanish:", meta_ext.get("series_spanish"))
        print("  volume:", meta_ext.get("volume"))
        print("  uuid:", meta_ext.get("uuid"))
        print("  asin:", meta_ext.get("asin"))
        assert meta_ext.get("spanish_title") == "Eminencia en las Sombras, Vol. 5"
        assert meta_ext.get("series_spanish") == "Eminencia en las Sombras"
        assert meta_ext.get("volume") == 5.0
        assert meta_ext.get("uuid") == "01924b89-9132-73a4-9419-f53e20e6a8d0"
        assert meta_ext.get("asin") == "B0BXYZ1234"
        assert meta_ext.get("editor") == "Zack"
        assert meta_ext.get("publisher_url") == "https://fansub.org"

        # Test process_book_identity_comprehensive
        identity = process_book_identity_comprehensive(
            meta=meta_ext, original_filename="Eminencia en las Sombras - 05.epub"
        )
        print("Test E (process_book_identity_comprehensive):")
        print("  series:", identity.get("series"))
        print("  volume:", identity.get("volume"))
        print("  spanish_title:", identity.get("spanish_title"))
        print("  uuid:", identity.get("uuid"))
        print("  asin:", identity.get("asin"))
        print("  editor:", identity.get("editor"))
        assert identity.get("series") == "Eminencia en las Sombras"
        assert identity.get("volume") == 5.0
        assert identity.get("uuid") == "01924b89-9132-73a4-9419-f53e20e6a8d0"
        assert identity.get("asin") == "B0BXYZ1234"
        assert identity.get("editor") == "Zack"
        print("-> Test D y E PASADOS OK!\n")
    finally:
        import os

        try:
            os.remove(tmp_path)
        except Exception:
            pass

    # 5. Test Standalone con EpubMetadataExtractor
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp_b:
        tmp_b.write(epub_bytes_b)
        tmp_b_path = tmp_b.name

    try:
        extractor_b = EpubMetadataExtractor(tmp_b_path)
        meta_b = extractor_b.extract()
        identity_b = process_book_identity_comprehensive(
            meta=meta_b, original_filename="Quiero Comerme tu Pancreas.epub"
        )
        print("Test F (Standalone process_book_identity_comprehensive):")
        print("  series:", identity_b.get("series"))
        print("  volume:", identity_b.get("volume"))
        print("  title:", identity_b.get("title"))
        assert identity_b.get("series") == "Quiero Comerme tu Páncreas"
        assert identity_b.get("series") != "Unknown"
        assert identity_b.get("volume") == 1.0
        print("-> Test F PASADO OK!\n")
    finally:
        import os

        try:
            os.remove(tmp_b_path)
        except Exception:
            pass

    print("=== TODOS LOS TESTS PASARON EXITOSAMENTE ===")


if __name__ == "__main__":
    asyncio.run(test_all())
