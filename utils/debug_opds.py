import feedparser
import sys
import os

# Add parent directory to path to allow importing utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import extract_author

xml_data = """
<entry>
<updated>2026-01-06T18:14:03</updated>
<id>90</id>
<title>A Certain Magical Index: Road to Endymion [NL]</title>
<summary>Format: Epub Summary: ...</summary>
<link rel="subsection" type="application/atom+xml;profile=opds-catalog;kind=navigation" href="/api/opds/series/90"/>
<author>
<name>Haimura Kiyotaka</name>
<uri>http://opds-spec.org/author/222</uri>
</author>
<author>
<name>Kazuma Kamachi</name>
<uri>http://opds-spec.org/author/10</uri>
</author>
<category term="" label="Acción"/>
<category term="" label="Chicos/shounen"/>
<category term="" label="Ciencia ficción"/>
<category term="" label="Comedia"/>
<category term="" label="Drama"/>
<category term="" label="Fantasía"/>
<category term="" label="Juvenil"/>
<category term="" label="Romance"/>
<category term="" label="Sobrenatural"/>
</entry>
"""

# Simulate feed parsing
feed = feedparser.parse(xml_data)
entry = feed.entries[0]

print("--- Data Extraction Debug ---")
print(f"Title: {entry.title}")

# Test Author Extraction
print(f"\nRaw entry.authors: {getattr(entry, 'authors', 'Not Found')}")
extracted_author = extract_author(entry)
print(f"Extracted Author: {extracted_author}")

# Test Category Extraction
categories = [
    tag.get("label") or tag.get("term")
    for tag in getattr(entry, "tags", [])
    if tag.get("label") or tag.get("term")
]
print(f"\nRaw entry.tags: {getattr(entry, 'tags', 'Not Found')}")
print(f"Extracted Categories: {categories}")

print("\n--- Expected vs Actual ---")
expected_author = "Haimura Kiyotaka - Kazuma Kamachi"
expected_categories = ['Acción', 'Chicos/shounen', 'Ciencia ficción', 'Comedia', 'Drama', 'Fantasía', 'Juvenil', 'Romance', 'Sobrenatural']

if extracted_author == expected_author:
    print("✅ Author extraction SUCCESS")
else:
    print(f"❌ Author extraction FAILED. Expected '{expected_author}', got '{extracted_author}'")

if categories == expected_categories:
    print("✅ Category extraction SUCCESS")
else:
    print(f"❌ Category extraction FAILED. Expected {expected_categories}, got {categories}")
