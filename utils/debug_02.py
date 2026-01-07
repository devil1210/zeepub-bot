import feedparser
import httpx
import asyncio
from config.config_settings import config

async def debug_feed():
    # USAR UNA URL QUE TENGA LIBROS CON MULTIPLES AUTORES
    # La del usuario: https://zeepubs.com/api/opds/2fe0e6fc-c7e2-4d8b-869a-ed32d253d47d/libraries/1
    url = "https://zeepubs.com/api/opds/2fe0e6fc-c7e2-4d8b-869a-ed32d253d47d/libraries/1"
    auth = config.OPDS_AUTH
    
    print(f"DEBUG: Fetching {url}")
    async with httpx.AsyncClient(auth=auth, timeout=30) as client:
        resp = await client.get(url)
        content = resp.content
    
    feed = feedparser.parse(content)
    
    for entry in feed.entries:
        if "86" in entry.title or "Index" in entry.title:
            print(f"\n--- ENTRY: {entry.title} ---")
            print(f"Authors Key: {entry.get('authors')}")
            print(f"Author Key: {entry.get('author')}")
            print(f"Author Detail: {entry.get('author_detail')}")
            print(f"Tags: {entry.get('tags')}")
            # Check the raw entry to see if there are other author fields
            for k in entry.keys():
                if "author" in k or "creator" in k:
                    print(f"Found author-like key: {k} = {entry.get(k)}")

if __name__ == "__main__":
    asyncio.run(debug_feed())
