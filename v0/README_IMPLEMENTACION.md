# Guía de Implementación - ZeePub Mini App

## 1. Instalación Rápida

### Opción A: Descargar desde v0
1. Haz clic en los 3 puntos (⋯) arriba a la derecha
2. Selecciona "Download ZIP"
3. Extrae y copia todos los archivos a tu repositorio `zeepub-bot/zeepub-web/`
4. Haz commit y push

### Opción B: Copiar manualmente
Copia estos archivos a tu repositorio:

```
zeepub-bot/zeepub-web/
├── app/
│   ├── layout.tsx (actualizado)
│   ├── page.tsx (actualizado)
│   ├── globals.css (actualizado)
│   ├── search/page.tsx
│   ├── status/page.tsx
│   ├── settings/page.tsx
│   ├── book/[id]/page.tsx
│   ├── downloads/page.tsx
│   ├── links/page.tsx
│   ├── admin/access-control/page.tsx
│   ├── no-access/page.tsx
│   └── api/
│       ├── user/access/route.ts
│       └── admin/access-levels/route.ts
├── components/
│   ├── bottom-nav.tsx
│   ├── pagination.tsx
│   ├── access-guard.tsx
│   └── telegram-provider.tsx
├── hooks/
│   ├── use-telegram.ts
│   └── use-access-control.ts
└── lib/
    ├── telegram.ts
    └── api.ts
```

## 2. Configurar Variables de Entorno

Agrega a tu `.env` o en Vercel:

```env
BOT_TOKEN=tu_bot_token_aqui
BOT_BACKEND_URL=https://tu-backend.com
NEXT_PUBLIC_BOT_USERNAME=ZeePubBot
```

## 3. Backend SQLite - Agregar a tu Bot

### Migración de Base de Datos

Crea `zeepub-bot/migrations/add_miniapp_tables.py`:

```python
import sqlite3
from datetime import datetime

def migrate(db_path='data/bot.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla de configuración de acceso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS miniapp_access_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            allowed_levels TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER
        )
    ''')
    
    # Insertar configuración por defecto (todos los niveles tienen acceso)
    cursor.execute('''
        INSERT OR IGNORE INTO miniapp_access_config (id, allowed_levels) 
        VALUES (1, '["free", "basic", "premium", "vip"]')
    ''')
    
    # Tabla de auditoría
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS miniapp_access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Migración completada")

if __name__ == '__main__':
    migrate()
```

Ejecuta: `python migrations/add_miniapp_tables.py`

### Agregar Endpoints FastAPI

En tu `zeepub-bot/main.py` o archivo de rutas, agrega:

```python
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import sqlite3
import json
from typing import Optional

app = FastAPI()

# Función para validar initData de Telegram
def validate_telegram_data(init_data: str, bot_token: str) -> dict:
    from telegram import Update
    from telegram.ext import ContextTypes
    # Implementa validación según docs de Telegram
    # Por ahora retorna datos de prueba
    return {"user_id": 123456, "username": "testuser"}

# Función para obtener nivel de usuario
def get_user_level(user_id: int) -> str:
    conn = sqlite3.connect('data/bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT level FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'free'

# Endpoint: Verificar acceso
@app.get("/api/user/access")
async def check_access(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "No autorizado")
    
    init_data = authorization.replace("Bearer ", "")
    user_data = validate_telegram_data(init_data, BOT_TOKEN)
    user_id = user_data['user_id']
    
    # Obtener nivel del usuario
    user_level = get_user_level(user_id)
    
    # Obtener niveles permitidos
    conn = sqlite3.connect('data/bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT allowed_levels FROM miniapp_access_config WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    
    allowed_levels = json.loads(result[0]) if result else []
    has_access = user_level in allowed_levels
    
    return {
        "hasAccess": has_access,
        "userLevel": user_level,
        "isAdmin": user_level == "vip"  # Ajusta según tu lógica
    }

# Endpoint: Obtener configuración (solo admin)
@app.get("/api/admin/access-levels")
async def get_access_config(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "No autorizado")
    
    user_data = validate_telegram_data(authorization.replace("Bearer ", ""), BOT_TOKEN)
    user_level = get_user_level(user_data['user_id'])
    
    if user_level != "vip":  # Solo admins
        raise HTTPException(403, "No tienes permisos")
    
    conn = sqlite3.connect('data/bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT allowed_levels FROM miniapp_access_config WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    
    return {
        "allowedLevels": json.loads(result[0]) if result else []
    }

# Endpoint: Actualizar configuración (solo admin)
class AccessConfig(BaseModel):
    allowedLevels: list[str]

@app.post("/api/admin/access-levels")
async def update_access_config(
    config: AccessConfig,
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(401, "No autorizado")
    
    user_data = validate_telegram_data(authorization.replace("Bearer ", ""), BOT_TOKEN)
    user_id = user_data['user_id']
    user_level = get_user_level(user_id)
    
    if user_level != "vip":
        raise HTTPException(403, "No tienes permisos")
    
    conn = sqlite3.connect('data/bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE miniapp_access_config 
        SET allowed_levels = ?, updated_at = ?, updated_by = ?
        WHERE id = 1
    ''', (json.dumps(config.allowedLevels), datetime.now(), user_id))
    conn.commit()
    conn.close()
    
    return {"success": True}
```

## 4. Configurar en BotFather

1. Abre Telegram y busca `@BotFather`
2. Envía `/mybots`
3. Selecciona tu bot `@ZeePubBot`
4. Selecciona "Mini Apps"
5. Selecciona "Configure Main App"
6. Envía la URL de tu mini app: `https://tu-app.vercel.app`

## 5. Desplegar en Vercel

1. Conecta tu repositorio a Vercel
2. Configura las variables de entorno
3. Despliega automáticamente

## Características Implementadas

- Navegación bottom tipo Telegram
- Búsqueda de libros con paginación OPDS
- Página de detalle de libro con portada grande
- Control de acceso por niveles de usuario
- Panel de administración
- Página de estado y descargas
- Diseño dark/blue tipo BotFather

## Soporte

Si tienes problemas, verifica:
- Las variables de entorno están configuradas
- El backend FastAPI está corriendo
- La base de datos SQLite tiene las tablas necesarias
- El BOT_TOKEN es correcto
