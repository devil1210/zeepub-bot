# Implementación del Sistema de Control de Acceso - SQLite

## 📋 Resumen

Este documento detalla cómo implementar el sistema de control de acceso por niveles de usuario en tu bot ZeePub que usa SQLite.

## 🗄️ Estructura de Base de Datos (SQLite)

### 1. Tabla de Usuarios (Existente - Modificar)

```sql
-- Agregar columnas a la tabla users si no existen
ALTER TABLE users ADD COLUMN level TEXT DEFAULT 'reader';
-- Niveles: 'reader', 'vip', 'premium', 'publisher', 'admin'

ALTER TABLE users ADD COLUMN mini_app_access INTEGER DEFAULT 1;
-- 1 = tiene acceso, 0 = sin acceso
```

### 2. Nueva Tabla: Configuración de Niveles de Acceso

```sql
CREATE TABLE IF NOT EXISTS mini_app_access_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT UNIQUE NOT NULL,
    has_access INTEGER DEFAULT 1,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER
);

-- Insertar configuración por defecto
INSERT INTO mini_app_access_config (level, has_access, description) VALUES
    ('reader', 1, 'Usuarios básicos'),
    ('vip', 1, 'Usuarios VIP'),
    ('premium', 1, 'Usuarios Premium'),
    ('publisher', 1, 'Publicadores'),
    ('admin', 1, 'Administradores');
```

### 3. Tabla de Auditoría

```sql
CREATE TABLE IF NOT EXISTS mini_app_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    admin_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);
```

## 📁 Estructura de Archivos del Bot (Python)

Crea estos archivos en tu estructura existente:

```
repositories/
├── access_control_repository.py  # Nuevo

services/
├── access_control_service.py     # Nuevo

handlers/
├── mini_app_handlers.py          # Nuevo

api/
└── routes.py                      # Modificar existente
```

## 🔧 Implementación Backend

### 1. Repository Layer (`repositories/access_control_repository.py`)

```python
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AccessControlRepository:
    def __init__(self, db_path: str = "zeepub.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _get_connection(self):
        """Crea una conexión a SQLite"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """Inicializa las tablas necesarias"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Tabla de configuración de acceso
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mini_app_access_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT UNIQUE NOT NULL,
                    has_access INTEGER DEFAULT 1,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER
                )
            """)
            
            # Tabla de auditoría
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mini_app_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    admin_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            """)
            
            # Insertar niveles por defecto si no existen
            cursor.execute("SELECT COUNT(*) as count FROM mini_app_access_config")
            if cursor.fetchone()['count'] == 0:
                cursor.executemany(
                    "INSERT INTO mini_app_access_config (level, has_access, description) VALUES (?, ?, ?)",
                    [
                        ('reader', 1, 'Usuarios básicos'),
                        ('vip', 1, 'Usuarios VIP'),
                        ('premium', 1, 'Usuarios Premium'),
                        ('publisher', 1, 'Publicadores'),
                        ('admin', 1, 'Administradores'),
                    ]
                )
            
            # Agregar columnas a users si no existen
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN level TEXT DEFAULT 'reader'")
            except sqlite3.OperationalError:
                pass  # La columna ya existe
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN mini_app_access INTEGER DEFAULT 1")
            except sqlite3.OperationalError:
                pass  # La columna ya existe
            
            conn.commit()
            logger.info("Tablas de control de acceso inicializadas correctamente")
        except Exception as e:
            logger.error(f"Error inicializando tablas: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_user_access(self, user_id: int) -> Dict:
        """Obtiene información de acceso del usuario"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.level, u.mini_app_access, c.has_access as level_has_access
                FROM users u
                LEFT JOIN mini_app_access_config c ON u.level = c.level
                WHERE u.id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def check_user_has_access(self, user_id: int) -> bool:
        """Verifica si el usuario tiene acceso a la mini app"""
        access_info = self.get_user_access(user_id)
        if not access_info:
            return False
        
        # El usuario tiene acceso si:
        # 1. Su nivel tiene acceso habilitado (level_has_access = 1)
        # 2. Y no tiene restricción individual (mini_app_access = 1)
        return bool(access_info['level_has_access']) and bool(access_info['mini_app_access'])
    
    def get_access_config(self) -> List[Dict]:
        """Obtiene toda la configuración de niveles"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT level, has_access, description, updated_at
                FROM mini_app_access_config
                ORDER BY 
                    CASE level
                        WHEN 'reader' THEN 1
                        WHEN 'vip' THEN 2
                        WHEN 'premium' THEN 3
                        WHEN 'publisher' THEN 4
                        WHEN 'admin' THEN 5
                        ELSE 6
                    END
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def update_level_access(self, level: str, has_access: bool, admin_id: int) -> bool:
        """Actualiza el acceso de un nivel completo"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE mini_app_access_config
                SET has_access = ?, updated_at = ?, updated_by = ?
                WHERE level = ?
            """, (1 if has_access else 0, datetime.now(), admin_id, level))
            
            conn.commit()
            logger.info(f"Nivel {level} actualizado a has_access={has_access} por admin {admin_id}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando nivel {level}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_user_access(self, user_id: int, has_access: bool, admin_id: int, reason: str = None) -> bool:
        """Actualiza el acceso individual de un usuario"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Obtener valor anterior
            cursor.execute("SELECT mini_app_access FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            old_value = row['mini_app_access'] if row else None
            
            # Actualizar acceso
            cursor.execute("""
                UPDATE users
                SET mini_app_access = ?
                WHERE id = ?
            """, (1 if has_access else 0, user_id))
            
            # Log de auditoría
            cursor.execute("""
                INSERT INTO mini_app_access_log 
                (user_id, admin_id, action, old_value, new_value, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, admin_id, 'update_user_access', str(old_value), str(has_access), reason))
            
            conn.commit()
            logger.info(f"Usuario {user_id} acceso actualizado a {has_access} por admin {admin_id}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando usuario {user_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_access_stats(self) -> Dict:
        """Obtiene estadísticas de acceso"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total de usuarios por nivel
            cursor.execute("""
                SELECT level, COUNT(*) as count
                FROM users
                GROUP BY level
            """)
            stats['users_by_level'] = {row['level']: row['count'] for row in cursor.fetchall()}
            
            # Usuarios con acceso vs sin acceso
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN mini_app_access = 1 THEN 1 ELSE 0 END) as with_access,
                    SUM(CASE WHEN mini_app_access = 0 THEN 1 ELSE 0 END) as without_access
                FROM users
            """)
            access_row = cursor.fetchone()
            stats['access_summary'] = dict(access_row)
            
            # Niveles habilitados
            cursor.execute("""
                SELECT level, has_access
                FROM mini_app_access_config
            """)
            stats['level_config'] = {row['level']: bool(row['has_access']) for row in cursor.fetchall()}
            
            return stats
        finally:
            conn.close()
```

### 2. Service Layer (`services/access_control_service.py`)

```python
from repositories.access_control_repository import AccessControlRepository
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class AccessControlService:
    def __init__(self, db_path: str = "zeepub.db"):
        self.repository = AccessControlRepository(db_path)
    
    def check_user_access(self, user_id: int) -> bool:
        """Verifica si un usuario tiene acceso a la mini app"""
        try:
            return self.repository.check_user_has_access(user_id)
        except Exception as e:
            logger.error(f"Error verificando acceso del usuario {user_id}: {e}")
            return False  # Por seguridad, denegar acceso en caso de error
    
    def get_user_access_info(self, user_id: int) -> Dict:
        """Obtiene información detallada de acceso del usuario"""
        return self.repository.get_user_access(user_id)
    
    def get_all_levels_config(self) -> List[Dict]:
        """Obtiene la configuración de todos los niveles"""
        return self.repository.get_access_config()
    
    def toggle_level_access(self, level: str, admin_id: int) -> bool:
        """Alterna el acceso de un nivel completo"""
        current_config = self.repository.get_access_config()
        level_config = next((l for l in current_config if l['level'] == level), None)
        
        if not level_config:
            logger.error(f"Nivel {level} no encontrado")
            return False
        
        new_access = not bool(level_config['has_access'])
        return self.repository.update_level_access(level, new_access, admin_id)
    
    def set_level_access(self, level: str, has_access: bool, admin_id: int) -> bool:
        """Establece el acceso de un nivel específico"""
        return self.repository.update_level_access(level, has_access, admin_id)
    
    def set_user_access(self, user_id: int, has_access: bool, admin_id: int, reason: str = None) -> bool:
        """Establece el acceso individual de un usuario"""
        return self.repository.update_user_access(user_id, has_access, admin_id, reason)
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de acceso"""
        return self.repository.get_access_stats()
```

### 3. API Routes (`api/routes.py` - Agregar estos endpoints)

```python
from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from services.access_control_service import AccessControlService
from utils.security import validate_telegram_data
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
access_service = AccessControlService()

# Modelos Pydantic
class AccessCheckResponse(BaseModel):
    has_access: bool
    level: str
    reason: Optional[str] = None

class LevelConfig(BaseModel):
    level: str
    has_access: bool
    description: Optional[str]

class UpdateLevelAccessRequest(BaseModel):
    level: str
    has_access: bool

class StatsResponse(BaseModel):
    users_by_level: dict
    access_summary: dict
    level_config: dict

# Endpoints

@router.get("/user/access", response_model=AccessCheckResponse)
async def check_user_access(
    x_telegram_data: str = Header(None)
):
    """Verifica si el usuario actual tiene acceso a la mini app"""
    if not x_telegram_data:
        raise HTTPException(status_code=401, detail="No Telegram data provided")
    
    # Validar initData
    user_data = validate_telegram_data(x_telegram_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_id = user_data.get('id')
    
    # Verificar acceso
    has_access = access_service.check_user_access(user_id)
    access_info = access_service.get_user_access_info(user_id)
    
    if not has_access:
        reason = "Tu nivel de usuario no tiene acceso a esta funcionalidad"
        if access_info and not access_info.get('mini_app_access'):
            reason = "Tu acceso ha sido restringido por un administrador"
    else:
        reason = None
    
    return AccessCheckResponse(
        has_access=has_access,
        level=access_info.get('level', 'reader') if access_info else 'reader',
        reason=reason
    )

@router.get("/admin/access-levels", response_model=List[LevelConfig])
async def get_access_levels_config(
    x_telegram_data: str = Header(None)
):
    """Obtiene la configuración de niveles (Solo Admin)"""
    if not x_telegram_data:
        raise HTTPException(status_code=401, detail="No Telegram data provided")
    
    user_data = validate_telegram_data(x_telegram_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_id = user_data.get('id')
    
    # Verificar si es admin (importar desde config)
    from config.config_settings import ADMIN_USERS
    if user_id not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    config = access_service.get_all_levels_config()
    return [LevelConfig(**level) for level in config]

@router.put("/admin/access-levels")
async def update_level_access(
    request: UpdateLevelAccessRequest,
    x_telegram_data: str = Header(None)
):
    """Actualiza el acceso de un nivel (Solo Admin)"""
    if not x_telegram_data:
        raise HTTPException(status_code=401, detail="No Telegram data provided")
    
    user_data = validate_telegram_data(x_telegram_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_id = user_data.get('id')
    
    # Verificar si es admin
    from config.config_settings import ADMIN_USERS
    if user_id not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Actualizar nivel
    success = access_service.set_level_access(
        request.level,
        request.has_access,
        user_id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update level access")
    
    return {"success": True, "message": f"Nivel {request.level} actualizado correctamente"}

@router.get("/admin/access-stats", response_model=StatsResponse)
async def get_access_stats(
    x_telegram_data: str = Header(None)
):
    """Obtiene estadísticas de acceso (Solo Admin)"""
    if not x_telegram_data:
        raise HTTPException(status_code=401, detail="No Telegram data provided")
    
    user_data = validate_telegram_data(x_telegram_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_id = user_data.get('id')
    
    from config.config_settings import ADMIN_USERS
    if user_id not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stats = access_service.get_stats()
    return StatsResponse(**stats)
```

## 📱 Frontend (Mini App Next.js)

Los archivos del frontend ya están creados en tu proyecto. Solo necesitas asegurarte de que están en la carpeta correcta.

## 🚀 Pasos de Implementación

### 1. Crear archivos Python en el bot

```bash
# En tu repositorio zeepub-bot
cd repositories
# Crear access_control_repository.py (copiar código de arriba)

cd ../services
# Crear access_control_service.py (copiar código de arriba)

cd ../api
# Editar routes.py y agregar los nuevos endpoints
```

### 2. Actualizar la base de datos

```bash
# Ejecutar el bot una vez para que se creen las tablas automáticamente
# O ejecutar manualmente el SQL en SQLite
sqlite3 zeepub.db < migration.sql
```

### 3. Desplegar el frontend

```bash
# La mini app debe estar en zeepub-web/ o zeepub-miniapp/
# según tu estructura actual

# Si usas zeepub-miniapp, renombra a zeepub-web
mv zeepub-miniapp zeepub-web

# Copia los archivos del proyecto v0 a zeepub-web/
```

### 4. Rebuild y restart

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## ✅ Verificación

1. **Base de datos**: Verifica que las tablas se crearon
```bash
sqlite3 zeepub.db ".tables"
# Deberías ver: mini_app_access_config, mini_app_access_log
```

2. **API**: Prueba el endpoint
```bash
curl -X GET https://tu-dominio.com/api/admin/access-levels \
  -H "X-Telegram-Data: <initData>"
```

3. **Mini App**: Abre la mini app en Telegram y verifica que el panel de admin aparece en Settings

## 🎨 Flujo de Usuario

### Para Administradores:

1. Abrir mini app en Telegram
2. Ir a "Settings" (Ajustes)
3. Click en "Control de Acceso" (solo visible para admins)
4. Ver lista de niveles con switches
5. Activar/desactivar niveles según necesidad
6. Ver estadísticas de acceso

### Para Usuarios Sin Acceso:

1. Abrir mini app
2. Ver pantalla "Sin Acceso" con mensaje claro
3. Información de contacto para solicitar acceso

## 🔒 Seguridad

- Todos los endpoints de admin validan `ADMIN_USERS` de tu config
- Validación de `initData` en cada request
- Logs de auditoría en cada cambio
- SQLite con protección contra SQL injection (prepared statements)
