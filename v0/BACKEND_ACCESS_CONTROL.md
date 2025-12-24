# Backend: Implementación del Control de Acceso

Esta guía explica cómo implementar el sistema de control de acceso por niveles de usuario en el backend Python de ZeePubBot.

## 📋 Índice

1. [Esquema de Base de Datos](#esquema-de-base-de-datos)
2. [Endpoints API](#endpoints-api)
3. [Validación de Telegram InitData](#validación-de-telegram-initdata)
4. [Middleware de Control de Acceso](#middleware-de-control-de-acceso)
5. [Ejemplos de Uso](#ejemplos-de-uso)

---

## 1. Esquema de Base de Datos

### Tabla: `user_levels`

Almacena los diferentes niveles de usuario y sus permisos.

```sql
CREATE TABLE IF NOT EXISTS user_levels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    priority INTEGER NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#5EAEE6',
    has_mini_app_access BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Niveles iniciales
INSERT INTO user_levels (name, priority, color, has_mini_app_access) VALUES
    ('Administrador', 10, '#FF6B6B', true),
    ('Premium', 5, '#4CAF50', true),
    ('Lector', 3, '#5EAEE6', true),
    ('Básico', 1, '#9E9E9E', false);
```

### Tabla: `users` (actualización)

Agregar columna `level_id` para vincular usuarios con niveles.

```sql
ALTER TABLE users 
ADD COLUMN level_id INTEGER REFERENCES user_levels(id) DEFAULT 1;

-- Crear índice para mejorar consultas
CREATE INDEX idx_users_level_id ON users(level_id);
```

### Tabla: `admins`

Lista de administradores con acceso al panel de control.

```sql
CREATE TABLE IF NOT EXISTS admins (
    user_id BIGINT PRIMARY KEY REFERENCES users(telegram_id),
    granted_by BIGINT REFERENCES users(telegram_id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Endpoints API

### 2.1. Verificar Acceso del Usuario

**Endpoint:** `POST /api/user/access`

**Descripción:** Verifica si un usuario tiene acceso a la Mini App.

**Request:**
```json
{
  "user_id": 123456789
}
```

**Response:**
```json
{
  "level": {
    "id": "3",
    "name": "Lector",
    "priority": 3,
    "color": "#5EAEE6",
    "hasAccess": true
  },
  "hasAccess": true,
  "isAdmin": false
}
```

**Implementación (FastAPI):**

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncpg

router = APIRouter()

class AccessCheckRequest(BaseModel):
    user_id: int

class UserLevel(BaseModel):
    id: str
    name: str
    priority: int
    color: str
    hasAccess: bool

class AccessResponse(BaseModel):
    level: UserLevel
    hasAccess: bool
    isAdmin: bool

@router.post("/api/user/access", response_model=AccessResponse)
async def check_user_access(
    request: AccessCheckRequest,
    db: asyncpg.Connection = Depends(get_db)
):
    # Obtener información del usuario y su nivel
    query = """
        SELECT 
            ul.id,
            ul.name,
            ul.priority,
            ul.color,
            ul.has_mini_app_access,
            EXISTS(SELECT 1 FROM admins WHERE user_id = $1) as is_admin
        FROM users u
        INNER JOIN user_levels ul ON u.level_id = ul.id
        WHERE u.telegram_id = $1
    """
    
    row = await db.fetchrow(query, request.user_id)
    
    if not row:
        # Usuario no existe, crear con nivel básico
        await db.execute(
            "INSERT INTO users (telegram_id, level_id) VALUES ($1, 1)",
            request.user_id
        )
        # Obtener nivel básico
        row = await db.fetchrow(query, request.user_id)
    
    return AccessResponse(
        level=UserLevel(
            id=str(row['id']),
            name=row['name'],
            priority=row['priority'],
            color=row['color'],
            hasAccess=row['has_mini_app_access']
        ),
        hasAccess=row['has_mini_app_access'],
        isAdmin=row['is_admin']
    )
```

### 2.2. Obtener Niveles (Admin)

**Endpoint:** `GET /api/admin/levels`

**Headers:** `Authorization: Bearer {BOT_TOKEN}`

**Response:**
```json
{
  "levels": [
    {
      "id": "1",
      "name": "Básico",
      "priority": 1,
      "color": "#9E9E9E",
      "hasAccess": false
    },
    {
      "id": "3",
      "name": "Lector",
      "priority": 3,
      "color": "#5EAEE6",
      "hasAccess": true
    }
  ]
}
```

**Implementación:**

```python
@router.get("/api/admin/levels")
async def get_levels(
    db: asyncpg.Connection = Depends(get_db),
    is_admin: bool = Depends(verify_admin)
):
    if not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    query = """
        SELECT id, name, priority, color, has_mini_app_access as "hasAccess"
        FROM user_levels
        ORDER BY priority DESC
    """
    
    rows = await db.fetch(query)
    
    levels = [
        {
            "id": str(row['id']),
            "name": row['name'],
            "priority": row['priority'],
            "color": row['color'],
            "hasAccess": row['hasAccess']
        }
        for row in rows
    ]
    
    return {"levels": levels}
```

### 2.3. Actualizar Niveles (Admin)

**Endpoint:** `PUT /api/admin/levels`

**Headers:** `Authorization: Bearer {BOT_TOKEN}`

**Request:**
```json
{
  "levels": [
    { "id": "1", "hasAccess": false },
    { "id": "3", "hasAccess": true }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Niveles actualizados correctamente"
}
```

**Implementación:**

```python
class LevelUpdate(BaseModel):
    id: str
    hasAccess: bool

class UpdateLevelsRequest(BaseModel):
    levels: list[LevelUpdate]

@router.put("/api/admin/levels")
async def update_levels(
    request: UpdateLevelsRequest,
    db: asyncpg.Connection = Depends(get_db),
    is_admin: bool = Depends(verify_admin)
):
    if not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    async with db.transaction():
        for level in request.levels:
            await db.execute(
                """
                UPDATE user_levels 
                SET has_mini_app_access = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                level.hasAccess,
                int(level.id)
            )
    
    return {
        "success": True,
        "message": "Niveles actualizados correctamente"
    }
```

---

## 3. Validación de Telegram InitData

Para validar que las peticiones vienen realmente de Telegram:

```python
import hmac
import hashlib
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException

def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Valida los datos de inicialización de Telegram Web App.
    """
    try:
        # Parsear los datos
        parsed_data = dict(parse_qsl(init_data))
        
        # Extraer hash
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            raise ValueError("Missing hash")
        
        # Construir data_check_string
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = '\n'.join(data_check_arr)
        
        # Generar secret_key
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calcular hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verificar
        if calculated_hash != received_hash:
            raise ValueError("Invalid hash")
        
        return parsed_data
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid init data: {str(e)}")

# Dependency para validar init data
async def get_telegram_user(
    x_telegram_init_data: str = Header(None)
) -> dict:
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing init data")
    
    bot_token = os.getenv("BOT_TOKEN")
    return validate_telegram_init_data(x_telegram_init_data, bot_token)
```

---

## 4. Middleware de Control de Acceso

Crear un decorador para proteger endpoints:

```python
from functools import wraps

def require_mini_app_access(func):
    """
    Decorador para requerir acceso a Mini App.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Obtener user_id del contexto
        user_id = kwargs.get('user_id') or args[0].user_id
        
        # Verificar acceso
        db = kwargs.get('db')
        has_access = await db.fetchval(
            """
            SELECT ul.has_mini_app_access
            FROM users u
            INNER JOIN user_levels ul ON u.level_id = ul.id
            WHERE u.telegram_id = $1
            """,
            user_id
        )
        
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="Tu nivel de usuario no tiene acceso a la Mini App"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper

# Uso
@router.post("/api/search")
@require_mini_app_access
async def search_books(request: SearchRequest, db = Depends(get_db)):
    # Lógica de búsqueda
    pass
```

---

## 5. Ejemplos de Uso

### Verificar acceso al iniciar la Mini App

```python
# En el endpoint de inicialización
@router.post("/api/init")
async def init_mini_app(
    telegram_user: dict = Depends(get_telegram_user),
    db: asyncpg.Connection = Depends(get_db)
):
    user_id = telegram_user['id']
    
    # Verificar acceso
    access_info = await check_user_access(
        AccessCheckRequest(user_id=user_id),
        db
    )
    
    if not access_info.hasAccess:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado"
        )
    
    return {
        "user": telegram_user,
        "access": access_info
    }
```

### Actualizar nivel de usuario desde el bot

```python
async def upgrade_user_level(telegram_id: int, new_level_name: str):
    """
    Actualiza el nivel de un usuario.
    """
    async with get_db_connection() as db:
        await db.execute(
            """
            UPDATE users
            SET level_id = (SELECT id FROM user_levels WHERE name = $1)
            WHERE telegram_id = $2
            """,
            new_level_name,
            telegram_id
        )
```

---

## 🔒 Seguridad

- **Validar siempre** el `initData` en el backend
- **No confiar** en validaciones del frontend
- **Usar HTTPS** en producción
- **Rotar tokens** periódicamente
- **Registrar** intentos de acceso no autorizado

---

## 📝 Notas Importantes

1. Los administradores siempre tienen acceso sin importar su nivel
2. Cambios en niveles se aplican inmediatamente
3. Usuarios nuevos se crean automáticamente con nivel básico
4. El control de acceso se verifica en cada request al backend
