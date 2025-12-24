# Implementación de Paginación en el Backend

Para que la paginación funcione correctamente, el backend debe modificarse para:

## 1. Endpoint de Búsqueda con Paginación

```python
from fastapi import APIRouter, Header, HTTPException
import feedparser
from urllib.parse import urljoin

router = APIRouter()

@router.post("/api/bot")
async def bot_api(
    action: str,
    data: dict,
    authorization: str = Header(None)
):
    # Validar initData de Telegram aquí
    
    if action == "search":
        query = data.get("query")
        page_url = data.get("pageUrl")  # URL de OPDS para paginación
        
        # Si hay pageUrl, usar esa. Si no, construir búsqueda inicial
        if page_url:
            feed_url = page_url
        else:
            # Construir URL de búsqueda OPDS
            feed_url = f"https://tu-opds-server.com/search?query={query}"
        
        # Parsear feed OPDS
        feed = feedparser.parse(feed_url)
        
        # Extraer libros
        books = []
        for entry in feed.entries[:20]:  # Primeros 20 resultados
            books.append({
                "id": entry.id,
                "title": entry.title,
                "author": entry.get("author", "Desconocido"),
                "year": entry.get("published", "")[:4],
                "size": entry.get("size", ""),
                "cover": entry.get("cover", "")
            })
        
        # Extraer links de navegación OPDS
        next_page = None
        prev_page = None
        
        for link in feed.feed.links:
            if link.rel == "next":
                next_page = urljoin(feed_url, link.href)
            elif link.rel == "previous":
                prev_page = urljoin(feed_url, link.href)
        
        # Extraer info de paginación si está disponible
        total_results = feed.feed.get("opensearch_totalresults", 0)
        items_per_page = feed.feed.get("opensearch_itemsperpage", 20)
        start_index = feed.feed.get("opensearch_startindex", 0)
        
        current_page = (start_index // items_per_page) + 1 if items_per_page > 0 else 1
        total_pages = (total_results // items_per_page) + 1 if items_per_page > 0 else None
        
        return {
            "results": books,
            "nextPage": next_page,
            "prevPage": prev_page,
            "currentPage": current_page,
            "totalPages": total_pages
        }
```

## 2. Estructura de Respuesta OPDS

El backend debe parsear estos elementos del feed OPDS:

### Links de Navegación
```xml
<link rel="next" href="/search?q=python&page=2" type="application/atom+xml"/>
<link rel="previous" href="/search?q=python&page=1" type="application/atom+xml"/>
```

### Metadatos OpenSearch
```xml
<opensearch:totalResults>156</opensearch:totalResults>
<opensearch:startIndex>20</opensearch:startIndex>
<opensearch:itemsPerPage>20</opensearch:itemsPerPage>
```

## 3. Ejemplo de Respuesta JSON

```json
{
  "results": [
    {
      "id": "book-123",
      "title": "El Quijote",
      "author": "Miguel de Cervantes",
      "year": "1605",
      "size": "2.4 MB",
      "cover": "https://example.com/cover.jpg"
    }
  ],
  "nextPage": "https://opds-server.com/search?query=python&page=2",
  "prevPage": null,
  "currentPage": 1,
  "totalPages": 8
}
```

## 4. Instalación de Dependencias

```bash
pip install feedparser
```

## 5. Manejo de Errores

```python
try:
    feed = feedparser.parse(feed_url)
    if feed.bozo:  # Error en el feed
        raise HTTPException(status_code=500, detail="Error al parsear OPDS")
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
