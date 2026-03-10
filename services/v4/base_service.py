import logging

from core.db_manager_pg import PostgresManager, pg_manager


class BaseService:
    """
    Blueprint for all V4 Services.
    Handles business logic entirely decoupled from Telegram types and Session management.
    Relies on provided DatabaseManager or specific Repositories.
    """

    def __init__(self, db_manager: PostgresManager | None = None):
        self.db = db_manager or pg_manager
        self.logger = logging.getLogger(self.__class__.__name__)
