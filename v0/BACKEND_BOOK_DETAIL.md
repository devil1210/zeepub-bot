# Backend: Endpoint de Detalles del Libro

## Nuevo Endpoint Requerido

Para que la página de detalles del libro funcione correctamente, necesitas agregar un nuevo endpoint en tu backend Python.

## FastAPI Implementation

```python
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import feedparser

router = APIRouter()

@router.post("/api/bot")
async def bot_api(
    request: dict,
    x_telegram_init_data: Optional[str] = Header(None)
):
    """
    Endpoint unificado para manejar todas las acciones de la mini app
    """
    
    # Validar initData de Telegram (importante para seguridad)
    if not validate_telegram_init_data(x_telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    action = request.get("action")
    data = request.get("data", {})
    
    if action == "book-detail":
        return await get_book_detail(data.get("bookId"))
    elif action == "search":
        return await search_books(data.get("query"), data.get("pageUrl"))
    elif action == "download":
        return await download_book(data.get("bookId"))
    else:
        raise HTTPException(status_code=400, detail="Unknown action")


async def get_book_detail(book_id: str):
    """
    Obtiene los detalles completos de un libro desde el OPDS feed
    
    Args:
        book_id: ID del libro (normalmente es la URL del entry OPDS)
    
    Returns:
        dict con toda la información del libro
    """
    try:
        # El book_id normalmente contiene la URL del entry OPDS
        # Parsea el feed OPDS para obtener el entry específico
        feed = feedparser.parse(book_id)
        
        if not feed.entries:
            raise HTTPException(status_code=404, detail="Book not found")
        
        entry = feed.entries[0]
        
        # Extraer la portada del libro
        cover_url = None
        for link in entry.links:
            if link.get('rel') == 'http://opds-spec.org/image' or \
               link.get('type', '').startswith('image/'):
                cover_url = link.get('href')
                break
        
        # Extraer el enlace de descarga
        download_url = None
        file_type = None
        file_size = None
        for link in entry.links:
            if link.get('rel') == 'http://opds-spec.org/acquisition':
                download_url = link.get('href')
                file_type = link.get('type', '').split('/')[-1].upper()
                file_size = link.get('length')
                break
        
        # Formatear el tamaño del archivo
        if file_size:
            size_kb = int(file_size) / 1024
            if size_kb > 1024:
                file_size = f"{size_kb / 1024:.2f} MB"
            else:
                file_size = f"{size_kb:.2f} KB"
        
        # Extraer metadatos adicionales
        author = entry.get('author', 'Autor desconocido')
        if isinstance(author, list):
            author = ', '.join([a.get('name', '') for a in author])
        
        # Buscar campos Dublin Core
        summary = entry.get('summary', entry.get('description', ''))
        
        # Extraer publisher, language, ISBN del contenido
        publisher = None
        language = None
        isbn = None
        
        if hasattr(entry, 'publisher'):
            publisher = entry.publisher
        if hasattr(entry, 'language'):
            language = entry.language
        if hasattr(entry, 'identifier'):
            isbn = entry.identifier
        
        # Año de publicación
        year = None
        if hasattr(entry, 'published'):
            year = entry.published.split('-')[0] if '-' in entry.published else entry.published
        elif hasattr(entry, 'dc_date'):
            year = entry.dc_date.split('-')[0]
        
        return {
            "id": book_id,
            "title": entry.get('title', 'Sin título'),
            "author": author,
            "year": year,
            "size": file_size,
            "fileType": file_type,
            "summary": summary,
            "cover": cover_url,
            "publisher": publisher,
            "language": language,
            "isbn": isbn,
            "downloadUrl": download_url
        }
        
    except Exception as e:
        print(f"Error fetching book details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def validate_telegram_init_data(init_data: str) -> bool:
    """
    Valida que el initData provenga realmente de Telegram
    
    Args:
        init_data: String de initData de Telegram
    
    Returns:
        bool: True si es válido
    """
    if not init_data:
        return False
    
    # Implementar validación usando el BOT_TOKEN
    # Ver: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    import hmac
    import hashlib
    from urllib.parse import parse_qs
    
    try:
        parsed = parse_qs(init_data)
        hash_value = parsed.get('hash', [''])[0]
        
        # Crear data_check_string
        data_check_arr = []
        for key in sorted(parsed.keys()):
            if key != 'hash':
                data_check_arr.append(f"{key}={parsed[key][0]}")
        data_check_string = '\n'.join(data_check_arr)
        
        # Calcular secret_key
        secret_key = hmac.new(
            b"WebAppData",
            msg=os.getenv("BOT_TOKEN").encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Calcular hash
        calculated_hash = hmac.new(
            secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == hash_value
        
    except Exception as e:
        print(f"Validation error: {e}")
        return False
```

## Ejemplo de Respuesta

```json
{
  "id": "https://example.com/opds/entry/12345",
  "title": "Parasite in Love [NL]",
  "author": "Koisuru Kiseichuu",
  "year": "2021",
  "size": "211.45 KB",
  "fileType": "EPUB+ZIP",
  "summary": "La historia es sobre un hombre con tenencias compulsivas que le hacen imposible encontrar trabajo y una jovencita que se salta clase y ama...",
  "cover": "https://example.com/covers/12345.jpg",
  "publisher": "Sugaru Miaki",
  "language": "es",
  "isbn": "978-1234567890",
  "downloadUrl": "https://example.com/download/12345.epub"
}
```

## Campos del OPDS Feed

Los feeds OPDS típicamente contienen estos campos que puedes mapear:

- `title` → título del libro
- `author` → autor(es)
- `summary` o `content` → resumen/descripción
- `dc:publisher` → editorial
- `dc:language` → idioma
- `dc:issued` → año de publicación
- `dc:identifier` → ISBN
- `link[rel="http://opds-spec.org/image"]` → portada
- `link[rel="http://opds-spec.org/acquisition"]` → descarga
- `link[type]` → tipo de archivo
- `link[length]` → tamaño del archivo

## Integración con el Bot Existente

Si ya tienes lógica para parsear OPDS en tu bot actual (en `bot.py` o similar), puedes reutilizarla:

```python
# En tu archivo principal del bot
from your_opds_parser import parse_opds_entry

@router.post("/api/bot")
async def bot_api(request: dict, x_telegram_init_data: str = Header(None)):
    action = request.get("action")
    
    if action == "book-detail":
        book_id = request["data"]["bookId"]
        
        # Reutilizar tu parser existente
        book_data = parse_opds_entry(book_id)
        
        return {
            "id": book_id,
            "title": book_data.get("title"),
            "author": book_data.get("author"),
            "year": book_data.get("year"),
            "size": book_data.get("size"),
            "fileType": book_data.get("file_type"),
            "summary": book_data.get("summary"),
            "cover": book_data.get("cover_url"),
            "publisher": book_data.get("publisher"),
            "language": book_data.get("language"),
            "isbn": book_data.get("isbn"),
            "downloadUrl": book_data.get("download_url")
        }
```

## Testing

Puedes probar el endpoint con curl:

```bash
curl -X POST http://localhost:8000/api/bot \
  -H "Content-Type: application/json" \
  -H "x-telegram-init-data: query_id=..." \
  -d '{
    "action": "book-detail",
    "data": {
      "bookId": "https://example.com/opds/entry/12345"
    }
  }'
```

## Notas de Seguridad

1. **Siempre valida el initData** para asegurar que las peticiones vengan de Telegram
2. **Limita el rate** de peticiones por usuario
3. **Sanitiza el bookId** antes de hacer requests externos
4. **Maneja errores** apropiadamente para no exponer información sensible
