# Backend SQLite - Implementación Final para ZeePubBot

Esta guía detalla cómo integrar el control de acceso y funcionalidades de la Mini App con la estructura SQLite existente del bot ZeePubBot.

## 1. Esquema de Base de Datos SQLite

El bot usa SQLite con la siguiente estructura. Agregamos las tablas necesarias para el control de acceso:

### Tablas Existentes (mantener)

```sql
-- Usuarios del bot
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    level TEXT DEFAULT 'Lector',  -- Lector, VIP, Premium, Publisher, Admin
    is_banned INTEGER DEFAULT 0,
    downloads_today INTEGER DEFAULT 0,
    last_reset_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historial de descargas
CREATE TABLE IF NOT EXISTS download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_title TEXT NOT NULL,
    book_author TEXT,
    download_url TEXT,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- URLs acortadas (para links de descarga)
CREATE TABLE IF NOT EXISTS url_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    clicks INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### Nuevas Tablas para Mini App

```sql
-- Configuración de acceso por nivel
CREATE TABLE IF NOT EXISTS access_control (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT UNIQUE NOT NULL,  -- Lector, VIP, Premium, Publisher, Admin
    has_access INTEGER DEFAULT 1,  -- 1 = tiene acceso, 0 = bloqueado
    priority INTEGER DEFAULT 0,  -- Orden de prioridad
    color TEXT DEFAULT '#64B5F6',  -- Color para UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auditoría de cambios de acceso
CREATE TABLE IF NOT EXISTS access_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- 'grant_access', 'revoke_access'
    level TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_user_id) REFERENCES users(user_id)
);

-- Insertar niveles por defecto
INSERT OR IGNORE INTO access_control (level, has_access, priority, color) VALUES
    ('Admin', 1, 5, '#F44336'),
    ('Publisher', 1, 4, '#FF9800'),
    ('Premium', 1, 3, '#FFD700'),
    ('VIP', 1, 2, '#4CAF50'),
    ('Lector', 1, 1, '#64B5F6');
```

## 2. Repositorio de Acceso (repositories/access_repository.py)

```python
"""Repositorio para gestión de control de acceso"""
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime


class AccessRepository:
    def __init__(self, db_path: str = "data/zeepub.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Inicializa las tablas de control de acceso"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS access_control (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT UNIQUE NOT NULL,
                    has_access INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    color TEXT DEFAULT '#64B5F6',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS access_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    level TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_user_id) REFERENCES users(user_id)
                )
            """)
            
            # Insertar niveles por defecto
            levels = [
                ('Admin', 1, 5, '#F44336'),
                ('Publisher', 1, 4, '#FF9800'),
                ('Premium', 1, 3, '#FFD700'),
                ('VIP', 1, 2, '#4CAF50'),
                ('Lector', 1, 1, '#64B5F6')
            ]
            
            for level, access, priority, color in levels:
                conn.execute("""
                    INSERT OR IGNORE INTO access_control (level, has_access, priority, color)
                    VALUES (?, ?, ?, ?)
                """, (level, access, priority, color))
            
            conn.commit()
    
    def get_all_levels(self) -> List[Dict]:
        """Obtiene todos los niveles de acceso"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT level, has_access, priority, color
                FROM access_control
                ORDER BY priority DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def check_user_access(self, user_id: int) -> bool:
        """Verifica si un usuario tiene acceso a la Mini App"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT ac.has_access
                FROM users u
                JOIN access_control ac ON u.level = ac.level
                WHERE u.user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            return bool(row[0]) if row else False
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Obtiene información del usuario incluyendo su nivel de acceso"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.first_name,
                    u.level,
                    u.is_banned,
                    ac.has_access,
                    ac.color
                FROM users u
                JOIN access_control ac ON u.level = ac.level
                WHERE u.user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_level_access(self, level: str, has_access: bool, admin_user_id: int) -> bool:
        """Actualiza el acceso de un nivel (solo admin)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Actualizar acceso
                conn.execute("""
                    UPDATE access_control
                    SET has_access = ?, updated_at = ?
                    WHERE level = ?
                """, (int(has_access), datetime.now(), level))
                
                # Registrar auditoría
                action = 'grant_access' if has_access else 'revoke_access'
                conn.execute("""
                    INSERT INTO access_audit (admin_user_id, action, level)
                    VALUES (?, ?, ?)
                """, (admin_user_id, action, level))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating level access: {e}")
            return False
    
    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        """Obtiene el log de auditoría de cambios de acceso"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    aa.action,
                    aa.level,
                    aa.timestamp,
                    u.username as admin_username,
                    u.first_name as admin_first_name
                FROM access_audit aa
                JOIN users u ON aa.admin_user_id = u.user_id
                ORDER BY aa.timestamp DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
```

## 3. API Routes en FastAPI (api/routes.py)

Agregar estos endpoints a tu archivo `api/routes.py`:

```python
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from utils.security import validate_telegram_data
from repositories.access_repository import AccessRepository

router = APIRouter()
access_repo = AccessRepository()


class UserAccessResponse(BaseModel):
    has_access: bool
    level: str
    is_admin: bool
    user_info: Optional[dict] = None


class LevelAccessUpdate(BaseModel):
    id: str
    hasAccess: bool


class AccessLevelsUpdate(BaseModel):
    levels: List[LevelAccessUpdate]
    initData: str


@router.get("/api/user/access")
async def check_user_access(
    x_telegram_data: Optional[str] = Header(None)
):
    """Verifica si el usuario tiene acceso a la Mini App"""
    if not x_telegram_data:
        raise HTTPException(status_code=401, detail="No Telegram data provided")
    
    # Validar datos de Telegram
    user_data = validate_telegram_data(x_telegram_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_id = user_data.get('id')
    
    # Obtener información del usuario
    user_info = access_repo.get_user_info(user_id)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar si está baneado
    if user_info['is_banned']:
        return UserAccessResponse(
            has_access=False,
            level=user_info['level'],
            is_admin=False,
            user_info=user_info
        )
    
    # Verificar acceso por nivel
    has_access = user_info['has_access']
    is_admin = user_info['level'] == 'Admin'
    
    return UserAccessResponse(
        has_access=has_access,
        level=user_info['level'],
        is_admin=is_admin,
        user_info=user_info
    )


@router.get("/api/admin/access-levels")
async def get_access_levels(
    x_telegram_data: Optional[str] = Header(None)
):
    """Obtiene todos los niveles de acceso (solo admin)"""
    if not x_telegram_data:
        raise HTTPException(status_code=401, detail="No Telegram data provided")
    
    # Validar que sea admin
    user_data = validate_telegram_data(x_telegram_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_id = user_data.get('id')
    user_info = access_repo.get_user_info(user_id)
    
    if not user_info or user_info['level'] != 'Admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    levels = access_repo.get_all_levels()
    
    # Formatear para el frontend
    formatted_levels = [
        {
            'id': level['level'],
            'name': level['level'],
            'hasAccess': bool(level['has_access']),
            'priority': level['priority'],
            'color': level['color']
        }
        for level in levels
    ]
    
    return {"levels": formatted_levels}


@router.post("/api/admin/access-levels")
async def update_access_levels(
    data: AccessLevelsUpdate,
    x_telegram_data: Optional[str] = Header(None)
):
    """Actualiza la configuración de niveles de acceso (solo admin)"""
    if not x_telegram_data:
        raise HTTPException(status_code=401, detail="No Telegram data provided")
    
    # Validar que sea admin
    user_data = validate_telegram_data(data.initData or x_telegram_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_id = user_data.get('id')
    user_info = access_repo.get_user_info(user_id)
    
    if not user_info or user_info['level'] != 'Admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Actualizar cada nivel
    success = True
    for level_update in data.levels:
        result = access_repo.update_level_access(
            level=level_update.id,
            has_access=level_update.hasAccess,
            admin_user_id=user_id
        )
        if not result:
            success = False
    
    return {"success": success, "message": "Access levels updated"}
```

## 4. Validación de Seguridad (utils/security.py)

```python
"""Validación de seguridad para Telegram Web Apps"""
import hmac
import hashlib
from urllib.parse import parse_qs
import os


def validate_telegram_data(init_data: str) -> dict:
    """
    Valida la firma criptográfica de initData de Telegram
    Retorna los datos del usuario si la validación es exitosa, None si falla
    """
    try:
        # Parsear los datos
        parsed_data = parse_qs(init_data)
        
        # Extraer el hash
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            return None
        
        # Construir data_check_string
        data_check_arr = []
        for key, values in sorted(parsed_data.items()):
            if key != 'hash':
                data_check_arr.append(f"{key}={values[0]}")
        
        data_check_string = '\n'.join(data_check_arr)
        
        # Obtener BOT_TOKEN del entorno
        bot_token = os.getenv('TELEGRAM_TOKEN')
        if not bot_token:
            return None
        
        # Calcular secret_key
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calcular hash esperado
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verificar hash
        if received_hash != expected_hash:
            return None
        
        # Extraer información del usuario
        import json
        user_data = json.loads(parsed_data.get('user', ['{}'])[0])
        
        return user_data
        
    except Exception as e:
        print(f"Error validating Telegram data: {e}")
        return None
```

## 5. Integración en el Bot Principal

Agregar al archivo `main.py` o `run_with_api.py`:

```python
# Importar el repositorio de acceso
from repositories.access_repository import AccessRepository

# Inicializar en el startup
access_repo = AccessRepository()

# Verificar acceso antes de permitir uso de comandos (opcional)
async def check_mini_app_access(user_id: int) -> bool:
    """Verifica si el usuario tiene acceso a funcionalidades de Mini App"""
    return access_repo.check_user_access(user_id)
```

## 6. Variables de Entorno

Asegúrate de tener estas variables en tu `.env`:

```bash
# Bot Token (necesario para validación de initData)
TELEGRAM_TOKEN=tu_bot_token_aqui

# Administradores (IDs separados por coma)
ADMIN_USERS=123456789,987654321

# Base de datos SQLite
DATABASE_PATH=data/zeepub.db

# Dominio público (para Mini App)
PUBLIC_DOMAIN=tu-dominio.com
```

## 7. Comandos de Testing

Puedes probar la integración con estos comandos SQL:

```sql
-- Ver todos los niveles y su acceso
SELECT * FROM access_control ORDER BY priority DESC;

-- Ver usuarios y su acceso
SELECT 
    u.user_id,
    u.username,
    u.level,
    ac.has_access
FROM users u
JOIN access_control ac ON u.level = ac.level;

-- Revocar acceso a nivel "Lector" manualmente
UPDATE access_control SET has_access = 0 WHERE level = 'Lector';

-- Ver log de auditoría
SELECT 
    aa.*,
    u.username as admin_username
FROM access_audit aa
JOIN users u ON aa.admin_user_id = u.user_id
ORDER BY timestamp DESC
LIMIT 10;
```

## Resumen

Con esta implementación tienes:

1. Tablas SQLite para control de acceso y auditoría
2. Repositorio Python para gestionar la base de datos
3. API endpoints en FastAPI para el frontend
4. Validación criptográfica de seguridad
5. Sistema de auditoría completo
6. Panel de administración funcional en la Mini App

Todos los cambios son compatibles con tu estructura existente de SQLite y no requieren PostgreSQL.
