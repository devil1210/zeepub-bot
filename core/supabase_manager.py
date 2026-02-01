import logging

from supabase import Client, create_client

from config.config_settings import config

logger = logging.getLogger(__name__)


class SupabaseManager:
    """Gestión de conexión y operaciones con Supabase."""

    def __init__(self):
        self.url = config.SUPABASE_URL
        self.key = config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_KEY
        self.client: Client | None = None

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
            raise RuntimeError(
                "Supabase client is not initialized. Check your credentials."
            )
        return self.client

    async def execute_query(self, table: str, query_type: str = "select", **kwargs):
        """Helper para ejecutar queries con reintento automático para errores 5xx."""
        if not self.is_active:
            return None

        max_retries = 3
        retry_delay = 1.0  # segundos

        for attempt in range(max_retries):
            try:
                query = self.client.table(table)
                if query_type == "select":
                    res = query.select("*").execute()
                elif query_type == "insert":
                    res = query.insert(kwargs.get("data")).execute()
                elif query_type == "update":
                    res = (
                        query.update(kwargs.get("data"))
                        .eq(kwargs.get("match_col"), kwargs.get("match_val"))
                        .execute()
                    )
                elif query_type == "delete":
                    res = (
                        query.delete()
                        .eq(kwargs.get("match_col"), kwargs.get("match_val"))
                        .execute()
                    )
                else:
                    logger.error(f"Unsupported query type: {query_type}")
                    return None
                return res
            except Exception as e:
                # Si es un error 502/503/504 o similar de red
                error_str = str(e)
                if any(
                    err in error_str
                    for err in [
                        "500",
                        "502",
                        "503",
                        "504",
                        "Bad Gateway",
                        "Service Unavailable",
                    ]
                ):
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Supabase transient error ({error_str}). Retrying {attempt + 1}/{max_retries} in {retry_delay}s..."
                        )
                        import asyncio

                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Backoff exponencial
                        continue

                logger.error(f"Supabase RPC Error [{table}.{query_type}]: {e}")
                return None
        return None


supabase_manager = SupabaseManager()
