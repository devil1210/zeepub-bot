
import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from config.config_settings import config

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Gestión de conexión y operaciones con Supabase."""

    def __init__(self):
        self.url = config.SUPABASE_URL
        self.key = config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_KEY
        self.client: Optional[Client] = None

        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Supabase client: {e}")

    @property
    def is_active(self) -> bool:
        return self.client is not None and config.ENABLE_SUPABASE

    def get_client(self) -> Client:
        if not self.client:
            raise RuntimeError("Supabase client is not initialized. Check your credentials.")
        return self.client

    async def execute_query(self, table: str, query_type: str = "select", **kwargs):
        """Helper para ejecutar queries comunes de forma asíncrona (vía supabase-py)."""
        if not self.is_active:
            return None
        
        # Nota: supabase-py es mayormente síncrono en su implementación actual bajo el capó,
        # pero para el bot lo manejaremos con cuidado.
        try:
            query = self.client.table(table)
            if query_type == "select":
                return query.select("*").execute()
            elif query_type == "insert":
                return query.insert(kwargs.get("data")).execute()
            elif query_type == "update":
                return query.update(kwargs.get("data")).eq(kwargs.get("match_col"), kwargs.get("match_val")).execute()
            elif query_type == "delete":
                return query.delete().eq(kwargs.get("match_col"), kwargs.get("match_val")).execute()
        except Exception as e:
            logger.error(f"Supabase RPC Error [{table}.{query_type}]: {e}")
            return None

supabase_manager = SupabaseManager()
