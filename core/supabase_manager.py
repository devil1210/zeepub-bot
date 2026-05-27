import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Mock SupabaseManager for V4/V5 PostgreSQL pure operation."""
    def __init__(self):
        self.url = ""
        self.key = ""
        self.client = None

    @property
    def is_active(self) -> bool:
        return False

    def get_client(self):
        raise RuntimeError("Supabase is disabled in this edition of ZeePub.")

supabase_manager = SupabaseManager()
