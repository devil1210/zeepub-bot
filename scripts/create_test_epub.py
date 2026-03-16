import os
import zipfile

test_dir = "test_library_v4"
os.makedirs(test_dir, exist_ok=True)
epub_path = os.path.join(test_dir, "TestBook.epub")

with zipfile.ZipFile(epub_path, "w") as z:
    z.writestr("mimetype", "application/epub+zip")
    z.writestr(
        "META-INF/container.xml",
        '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
    )
    z.writestr(
        "content.opf",
        '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" unique-identifier="pub-id" version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Test Book V4</dc:title><dc:creator>Kaguya Shinomiya</dc:creator><dc:language>es</dc:language><dc:identifier id="pub-id">test-v4</dc:identifier></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="c1" href="c1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>',
    )
    z.writestr(
        "nav.xhtml",
        '<html><body><nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc"><h1>TOC</h1></nav></body></html>',
    )
    z.writestr("c1.xhtml", "<html><body><p>Hello V4 Reference</p></body></html>")

print(f"Created test epub at {epub_path}")
