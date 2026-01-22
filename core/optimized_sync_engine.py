import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from sqlalchemy import select, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.user_models import User, UserLevel, UserUISettings
from services.cache_service import cache_manager

logger = logging.getLogger(__name__)

class OptimizedSyncEngine:
    """
    Motor de sincronización optimizado que reduce drásticamente las solicitudes a Supabase.
    
    Estrategia:
    - Event-driven en lugar de time-based polling
    - Batch processing para operaciones masivas
    - Cache inteligente para reducir consultas
    - Detección de cambios mediante timestamps
    """
    
    def __init__(self):
        self.running = False
        self.last_sync_times = {
            'users': datetime.min,
            'user_levels': datetime.min,
            'admins': datetime.min
        }
        self.pending_changes = {
            'users': set(),
            'user_levels': set(),
            'admins': set()
        }
        self.sync_intervals = {
            'users': 300,  # 5 minutos (solo si hay cambios)
            'user_levels': 3600,  # 1 hora (poco frecuente)
            'admins': 60  # 1 minuto (crítico pero bajo volumen)
        }
        
    async def start(self):
        """Inicia el motor de sincronización optimizado."""
        if self.running:
            return
            
        self.running = True
        logger.info("Optimized Sync Engine started")
        
        # Iniciar tareas en segundo plano
        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._change_detector_loop())
        
    async def stop(self):
        """Detiene el motor de sincronización."""
        self.running = False
        logger.info("Optimized Sync Engine stopped")
        
    async def _sync_loop(self):
        """Bucle principal de sincronización optimizado."""
        while self.running:
            try:
                if config.ENABLE_SUPABASE and config.ENABLE_POSTGRES_PLUGIN:
                    # Sincronizar solo si hay cambios pendientes
                    await self._sync_if_changed('users')
                    await self._sync_if_changed('user_levels')
                    await self._sync_if_changed('admins')
                    
            except Exception as e:
                logger.error(f"Error in optimized sync loop: {e}")
                
            # Esperar adaptativa basada en actividad
            await asyncio.sleep(30)  # Check every 30 seconds
            
    async def _change_detector_loop(self):
        """Bucle de detección de cambios."""
        while self.running:
            try:
                await self._detect_changes()
            except Exception as e:
                logger.error(f"Error in change detector: {e}")
                
            await asyncio.sleep(60)  # Check for changes every minute
            
    async def _detect_changes(self):
        """Detecta cambios en Supabase sin hacer polling constante."""
        if not supabase_manager.is_active:
            return
            
        try:
            # Detectar cambios en usuarios
            await self._detect_user_changes()
            
            # Detectar cambios en niveles (menos frecuente)
            if datetime.utcnow() - self.last_sync_times['user_levels'] > timedelta(hours=1):
                await self._detect_level_changes()
                
        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
            
    async def _detect_user_changes(self):
        """Detecta cambios en usuarios de Supabase."""
        try:
            # Usar timestamp differential query
            last_check = self.last_sync_times['users']
            
            # Query optimizada para obtener solo usuarios modificados
            result = supabase_manager.get_client().table('users')\
                .select("telegram_id, updated_at")\
                .gte("updated_at", last_check.isoformat())\
                .limit(100)\
                .execute()
                
            if result and result.data:
                changed_users = {item['telegram_id'] for item in result.data}
                self.pending_changes['users'].update(changed_users)
                
                if changed_users:
                    logger.info(f"Detected {len(changed_users)} user changes in Supabase")
                    
        except Exception as e:
            logger.error(f"Error detecting user changes: {e}")
            
    async def _detect_level_changes(self):
        """Detecta cambios en niveles de usuario."""
        try:
            result = supabase_manager.get_client().table('user_levels')\
                .select("id, updated_at")\
                .execute()
                
            if result and result.data:
                # Comparar con versión local
                local_levels = await self._get_local_level_ids()
                remote_levels = {item['id'] for item in result.data}
                
                if local_levels != remote_levels:
                    self.pending_changes['user_levels'].update(remote_levels)
                    logger.info("Detected user_levels changes")
                    
        except Exception as e:
            logger.error(f"Error detecting level changes: {e}")
            
    async def _get_local_level_ids(self) -> Set[int]:
        """Obtiene IDs de niveles locales."""
        try:
            async with pg_manager.get_session() as session:
                result = await session.execute(select(UserLevel.id))
                return {row[0] for row in result.fetchall()}
        except Exception as e:
            logger.error(f"Error getting local level IDs: {e}")
            return set()
            
    async def _sync_if_changed(self, table_name: str):
        """Sincroniza tabla solo si hay cambios pendientes."""
        if not self.pending_changes[table_name]:
            return
            
        # Verificar intervalo mínimo
        time_since_last = datetime.utcnow() - self.last_sync_times[table_name]
        if time_since_last < timedelta(seconds=self.sync_intervals[table_name]):
            return
            
        logger.info(f"Syncing {table_name} - {len(self.pending_changes[table_name])} changes pending")
        
        if table_name == 'users':
            await self._sync_users_optimized()
        elif table_name == 'user_levels':
            await self._sync_user_levels_optimized()
        elif table_name == 'admins':
            await self._sync_admins_optimized()
            
        # Limpiar cambios procesados y actualizar timestamp
        self.pending_changes[table_name].clear()
        self.last_sync_times[table_name] = datetime.utcnow()
        
    async def _sync_users_optimized(self):
        """Sincronización optimizada de usuarios."""
        if not supabase_manager.is_active:
            return
            
        try:
            # Obtener usuarios modificados de Supabase
            last_sync = self.last_sync_times['users']
            
            result = supabase_manager.get_client().table('users')\
                .select("*")\
                .gte("updated_at", last_sync.isoformat())\
                .order("updated_at", desc=True)\
                .limit(200)\
                .execute()
                
            if not result or not result.data:
                return
                
            # Batch update local
            await self._batch_update_users(result.data)
            
            # Invalidar caché de usuarios afectados
            for user_data in result.data:
                await cache_manager.invalidate_user(user_data['telegram_id'])
                
            logger.info(f"Synced {len(result.data)} users from Supabase to local")
            
        except Exception as e:
            logger.error(f"Error in optimized users sync: {e}")
            
    async def _batch_update_users(self, users_data: List[Dict[str, Any]]):
        """Actualización batch de usuarios en local."""
        try:
            async with pg_manager.get_session() as session:
                for user_data in users_data:
                    # Mapear datos de Supabase a modelo local
                    mapped_data = {
                        "telegram_id": user_data['telegram_id'],
                        "username": user_data.get('username'),
                        "name": user_data.get('name'),
                        "nickname": user_data.get('nickname'),
                        "level_id": user_data.get('level_id', 6),
                        "role": user_data.get('role', 'user'),
                        "beta_tester": user_data.get('beta_tester', False),
                        "has_library_access": user_data.get('has_library_access', True),
                        "can_request_books": user_data.get('can_request_books', True),
                        "total_downloads": user_data.get('total_downloads', 0),
                        "insignias": user_data.get('insignias', []),
                        "settings": user_data.get('settings', {}),
                        "expires_at": self._parse_datetime(user_data.get('expires_at')),
                        "updated_at": datetime.utcnow()
                    }
                    
                    # Upsert optimizado
                    await session.execute(
                        text("""
                            INSERT INTO users (
                                telegram_id, username, name, nickname, level_id, role,
                                beta_tester, has_library_access, can_request_books,
                                total_downloads, insignias, settings, expires_at, updated_at
                            ) VALUES (
                                :telegram_id, :username, :name, :nickname, :level_id, :role,
                                :beta_tester, :has_library_access, :can_request_books,
                                :total_downloads, :insignias, :settings, :expires_at, :updated_at
                            )
                            ON CONFLICT (telegram_id) DO UPDATE SET
                                username = EXCLUDED.username,
                                name = EXCLUDED.name,
                                nickname = EXCLUDED.nickname,
                                level_id = EXCLUDED.level_id,
                                role = EXCLUDED.role,
                                beta_tester = EXCLUDED.beta_tester,
                                has_library_access = EXCLUDED.has_library_access,
                                can_request_books = EXCLUDED.can_request_books,
                                total_downloads = EXCLUDED.total_downloads,
                                insignias = EXCLUDED.insignias,
                                settings = EXCLUDED.settings,
                                expires_at = EXCLUDED.expires_at,
                                updated_at = EXCLUDED.updated_at
                        """),
                        mapped_data
                    )
                    
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error in batch user update: {e}")
            raise
            
    async def _sync_user_levels_optimized(self):
        """Sincronización optimizada de niveles."""
        if not supabase_manager.is_active:
            return
            
        try:
            result = supabase_manager.get_client().table('user_levels')\
                .select("*")\
                .execute()
                
            if not result or not result.data:
                return
                
            await self._batch_update_levels(result.data)
            logger.info(f"Synced {len(result.data)} user levels from Supabase")
            
        except Exception as e:
            logger.error(f"Error in user levels sync: {e}")
            
    async def _batch_update_levels(self, levels_data: List[Dict[str, Any]]):
        """Actualización batch de niveles."""
        try:
            async with pg_manager.get_session() as session:
                for level_data in levels_data:
                    # Mapear datos
                    mapped_data = {
                        "id": level_data['id'],
                        "name": level_data['name'],
                        "priority": level_data.get('priority', 0),
                        "color": level_data.get('color', '#607D8B'),
                        "price": level_data.get('price', 0.0),
                        "can_download": level_data.get('can_download', True),
                        "can_read": level_data.get('can_read', True),
                        "daily_downloads": level_data.get('daily_downloads', 5),
                        "has_mini_app_access": level_data.get('has_mini_app_access', True),
                        "has_library_access": level_data.get('has_library_access', True),
                        "can_request_books": level_data.get('can_request_books', True),
                        "early_access": level_data.get('early_access', False),
                        "custom_themes": level_data.get('custom_themes', False),
                        "allow_theme_templates": level_data.get('allow_theme_templates', False),
                        "show_recommendations": level_data.get('show_recommendations', True),
                        "default_theme_id": level_data.get('default_theme_id'),
                        # ... otros campos de UI
                    }
                    
                    # Upsert
                    await session.execute(
                        text("""
                            INSERT INTO user_levels (
                                id, name, priority, color, price, can_download, can_read,
                                daily_downloads, has_mini_app_access, has_library_access,
                                can_request_books, early_access, custom_themes,
                                allow_theme_templates, show_recommendations, default_theme_id
                            ) VALUES (
                                :id, :name, :priority, :color, :price, :can_download, :can_read,
                                :daily_downloads, :has_mini_app_access, :has_library_access,
                                :can_request_books, :early_access, :custom_themes,
                                :allow_theme_templates, :show_recommendations, :default_theme_id
                            )
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                priority = EXCLUDED.priority,
                                color = EXCLUDED.color,
                                price = EXCLUDED.price,
                                can_download = EXCLUDED.can_download,
                                can_read = EXCLUDED.can_read,
                                daily_downloads = EXCLUDED.daily_downloads,
                                has_mini_app_access = EXCLUDED.has_mini_app_access,
                                has_library_access = EXCLUDED.has_library_access,
                                can_request_books = EXCLUDED.can_request_books,
                                early_access = EXCLUDED.early_access,
                                custom_themes = EXCLUDED.custom_themes,
                                allow_theme_templates = EXCLUDED.allow_theme_templates,
                                show_recommendations = EXCLUDED.show_recommendations,
                                default_theme_id = EXCLUDED.default_theme_id
                        """),
                        mapped_data
                    )
                    
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error in batch level update: {e}")
            raise
            
    async def _sync_admins_optimized(self):
        """Sincronización optimizada de admins."""
        if not supabase_manager.is_active:
            return
            
        try:
            result = supabase_manager.get_client().table('admins')\
                .select("*")\
                .execute()
                
            if not result or not result.data:
                return
                
            admin_ids = {item['user_id'] for item in result.data}
            await self._update_admins_table(admin_ids)
            
            logger.info(f"Synced {len(admin_ids)} admins from Supabase")
            
        except Exception as e:
            logger.error(f"Error in admins sync: {e}")
            
    async def _update_admins_table(self, admin_ids: Set[int]):
        """Actualiza tabla de admins."""
        try:
            async with pg_manager.get_session() as session:
                # Limpiar tabla actual
                await session.execute(text("DELETE FROM admins"))
                
                # Insertar admins actuales
                for admin_id in admin_ids:
                    await session.execute(
                        text("INSERT INTO admins (user_id) VALUES (:user_id)"),
                        {"user_id": admin_id}
                    )
                    
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating admins table: {e}")
            raise
            
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parsea datetime de Supabase."""
        if not dt_str:
            return None
            
        try:
            # Supabase envía ISO 8601 con Z
            dt_str = dt_str.replace('Z', '+00:00')
            return datetime.fromisoformat(dt_str).astimezone().replace(tzinfo=None)
        except Exception:
            return None
            
    async def mark_user_changed(self, telegram_id: int):
        """Marca un usuario como modificado para sincronización."""
        self.pending_changes['users'].add(telegram_id)
        
    async def mark_levels_changed(self):
        """Marca los niveles como modificados."""
        self.pending_changes['user_levels'].add('changed')
        
    async def force_sync_all(self):
        """Fuerza sincronización completa de todas las tablas."""
        logger.info("Forcing full sync of all tables")
        
        # Marcar todo como cambiado
        self.pending_changes['users'].add('force_sync')
        self.pending_changes['user_levels'].add('force_sync')
        self.pending_changes['admins'].add('force_sync')
        
        # Resetear timestamps para forzar sincronización
        for key in self.last_sync_times:
            self.last_sync_times[key] = datetime.min
            
    async def get_sync_status(self) -> Dict[str, Any]:
        """Obtiene estado actual de sincronización."""
        return {
            'running': self.running,
            'last_sync_times': {k: v.isoformat() for k, v in self.last_sync_times.items()},
            'pending_changes': {k: len(v) for k, v in self.pending_changes.items()},
            'supabase_active': supabase_manager.is_active,
            'postgres_enabled': config.ENABLE_POSTGRES_PLUGIN
        }

# Instancia global
optimized_sync_engine = OptimizedSyncEngine()
