# 🔌 Integración Backend Detallada

Esta guía explica cómo integrar la mini app con el backend Python existente de ZeePub.

## 📋 Resumen

La mini app se comunica con tu bot Python a través de una API REST. El flujo es:

```
Mini App (Next.js) → FastAPI Endpoint → Servicios del Bot → Base de Datos
```

## 🛠️ Paso 1: Actualizar FastAPI

### 1.1 Crear nuevos endpoints

Crea el archivo `api/miniapp_routes.py`:

```python
"""
Endpoints específicos para la Mini App de Telegram
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from utils.security import validate_init_data, get_user_from_init_data
from services.opds_service import search_books_in_catalog
from services.download_limiter import get_user_limits
from core.state_manager import StateManager
import os

router = APIRouter(prefix="/api/miniapp", tags=["miniapp"])

def verify_telegram_user(x_telegram_data: Optional[str] = Header(None)):
    """Dependency para verificar que la petición viene de Telegram"""
    if not x_telegram_data:
        raise HTTPException(status_code=401, detail="Missing Telegram data")
    
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not validate_init_data(x_telegram_data, bot_token):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    return get_user_from_init_data(x_telegram_data)

@router.get("/status")
async def get_bot_status(user=Depends(verify_telegram_user)):
    """Obtiene el estado actual del bot y límites del usuario"""
    try:
        limits = get_user_limits(user["id"])
        
        return {
            "status": "operational",
            "user": {
                "id": user["id"],
                "username": user.get("username"),
                "level": limits["level"],
                "downloads": {
                    "used": limits["downloads_used"],
                    "limit": limits["downloads_limit"],
                    "remaining": limits["downloads_remaining"],
                    "reset_time": limits["reset_time"]
                }
            },
            "bot": {
                "version": "4.2.0",
                "uptime": get_bot_uptime(),
                "features": {
                    "opds": True,
                    "evil_mode": user["id"] in get_admin_ids(),
                    "groups": True,
                    "mini_app": True
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_books(
    query: dict,
    user=Depends(verify_telegram_user)
):
    """Busca libros en el catálogo OPDS"""
    try:
        search_term = query.get("query", "")
        limit = query.get("limit", 20)
        
        # Determinar si usar catálogo evil
        is_admin = user["id"] in get_admin_ids()
        catalog = "evil" if is_admin and query.get("useEvil") else "normal"
        
        results = await search_books_in_catalog(
            search_term, 
            catalog=catalog,
            limit=limit
        )
        
        return {
            "results": results,
            "count": len(results),
            "catalog": catalog
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_user_settings(user=Depends(verify_telegram_user)):
    """Obtiene la configuración del usuario"""
    try:
        state = StateManager.get_user_state(user["id"])
        is_admin = user["id"] in get_admin_ids()
        
        return {
            "user_id": user["id"],
            "settings": {
                "inline_mode": state.get("inline_mode", False),
                "business_mode": state.get("business_mode", False),
                "groups": {
                    "allow_groups": state.get("allow_groups", True),
                    "group_privacy": state.get("group_privacy", True),
                    "group_admin_rights": state.get("group_admin_rights", 0),
                    "channel_admin_rights": state.get("channel_admin_rights", 0),
                },
                "admin_features": {
                    "enabled": is_admin,
                    "evil_mode": state.get("evil_mode", False) if is_admin else False,
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings")
async def update_user_settings(
    settings: dict,
    user=Depends(verify_telegram_user)
):
    """Actualiza la configuración del usuario"""
    try:
        user_id = user["id"]
        new_settings = settings.get("settings", {})
        
        # Actualizar estado
        StateManager.update_user_state(user_id, new_settings)
        
        return {
            "success": True,
            "message": "Settings updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download")
async def request_download(
    request: dict,
    user=Depends(verify_telegram_user)
):
    """Solicita la descarga de un libro"""
    try:
        book_url = request.get("url")
        
        # Verificar límites
        limits = get_user_limits(user["id"])
        if limits["downloads_remaining"] <= 0:
            raise HTTPException(
                status_code=429, 
                detail="Download limit reached"
            )
        
        # Procesar descarga (tu lógica existente)
        # ...
        
        return {
            "success": True,
            "message": "Download started",
            "downloads_remaining": limits["downloads_remaining"] - 1
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_admin_ids():
    """Obtiene lista de IDs de administradores"""
    admin_str = os.getenv("ADMIN_USERS", "")
    return [int(id) for id in admin_str.split(",") if id.strip()]

def get_bot_uptime():
    """Calcula el tiempo de actividad del bot"""
    # Implementa tu lógica aquí
    return "2 days, 3 hours"
```

### 1.2 Registrar las rutas

En `api/main.py` o `run_with_api.py`:

```python
from api.miniapp_routes import router as miniapp_router

# Registrar rutas
app.include_router(miniapp_router)
```

## 🔐 Paso 2: Actualizar Seguridad

Actualiza `utils/security.py`:

```python
import hmac
import hashlib
import json
from urllib.parse import parse_qs
from typing import Dict, Any

def validate_init_data(init_data: str, bot_token: str) -> bool:
    """
    Valida que los datos de inicialización vienen de Telegram
    Documentación: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed = parse_qs(init_data)
        hash_value = parsed.get("hash", [""])[0]
        
        if not hash_value:
            return False
        
        # Construir data-check-string
        data_check_arr = []
        for key in sorted(parsed.keys()):
            if key != "hash":
                value = parsed[key][0]
                data_check_arr.append(f"{key}={value}")
        
        data_check_string = "\n".join(data_check_arr)
        
        # Calcular hash esperado
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(hash_value, expected_hash)
        
    except Exception as e:
        print(f"Error validating init data: {e}")
        return False

def get_user_from_init_data(init_data: str) -> Dict[str, Any]:
    """Extrae información del usuario desde initData"""
    try:
        parsed = parse_qs(init_data)
        user_data = parsed.get("user", ["{}"])[0]
        user = json.loads(user_data)
        return user
    except Exception as e:
        print(f"Error parsing user data: {e}")
        return {}
```

## 🔄 Paso 3: Conectar con Servicios Existentes

### 3.1 Adaptar el servicio OPDS

En `services/opds_service.py`, asegúrate de tener:

```python
async def search_books_in_catalog(
    query: str, 
    catalog: str = "normal",
    limit: int = 20
):
    """
    Busca libros en el catálogo OPDS
    
    Args:
        query: Término de búsqueda
        catalog: "normal" o "evil"
        limit: Máximo de resultados
    
    Returns:
        Lista de libros con metadata
    """
    # Tu implementación existente
    pass
```

### 3.2 Adaptar el limitador de descargas

En `utils/download_limiter.py`:

```python
def get_user_limits(user_id: int) -> dict:
    """
    Obtiene los límites de descarga del usuario
    
    Returns:
        {
            "level": "Lector|VIP|Premium",
            "downloads_used": 3,
            "downloads_limit": 5,
            "downloads_remaining": 2,
            "reset_time": "2025-12-21 00:00:00"
        }
    """
    # Tu implementación existente
    pass
```

## 🌐 Paso 4: Configurar CORS

En `api/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

# Permitir peticiones desde la mini app
allowed_origins = [
    "https://zeepub-miniapp.vercel.app",  # Producción
    "https://*.vercel.app",                # Preview deployments
    "http://localhost:3000",               # Desarrollo local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## 🧪 Paso 5: Probar la Integración

### Test básico con curl:

```bash
# Obtener estado del bot
curl -X GET "https://tu-dominio.com/api/miniapp/status" \
  -H "X-Telegram-Data: query_id=AAH...&user=%7B%22id%22%3A123456789%7D&hash=abc123..."

# Buscar libros
curl -X POST "https://tu-dominio.com/api/miniapp/search" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Data: ..." \
  -d '{"query": "python", "limit": 10}'
```

## 📊 Paso 6: Logging y Monitoreo

Agrega logging para debugging:

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/search")
async def search_books(query: dict, user=Depends(verify_telegram_user)):
    logger.info(f"User {user['id']} searching for: {query.get('query')}")
    try:
        # ...
        logger.info(f"Found {len(results)} results")
        return {"results": results}
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise
```

## ✅ Checklist de Integración

- [ ] Endpoints de la API creados en `api/miniapp_routes.py`
- [ ] Rutas registradas en `api/main.py`
- [ ] Validación de `initData` implementada
- [ ] CORS configurado correctamente
- [ ] Servicios existentes adaptados (OPDS, límites)
- [ ] Logging configurado
- [ ] Tests básicos realizados
- [ ] Variables de entorno configuradas
- [ ] Bot reiniciado con `docker compose restart`

## 🐛 Debugging

Ver logs del backend:
```bash
docker logs zeepub_bot -f
```

Ver peticiones a la API:
```bash
docker logs zeepub_bot -f | grep "miniapp"
```

---

Con esta integración, tu mini app estará completamente conectada con el backend Python de ZeePub.
