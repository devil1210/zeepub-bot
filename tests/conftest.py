"""
Pytest configuration file.
Adds the project root to sys.path so tests can import project modules.
"""
import sys
import os
import pytest
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session", autouse=True)
def mock_staff_ids():
    """
    Ensures some default IDs are always in the staff lists for easy testing.
    """
    from config.config_settings import config
    config.ADMIN_USERS.add(12345)
    config.WHITELIST.add(11111)
    yield
    config.ADMIN_USERS.discard(12345)
    config.WHITELIST.discard(11111)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Ensures the database is initialized before any tests run.
    Uses a temporary database path to avoid side effects on the actual data.
    """
    from config.config_settings import config
    from core.db_manager import db_manager

    # Use a temporary database for testing
    test_db_path = os.path.join(project_root, "data/test_db.db")
    config.URL_CACHE_DB_PATH = test_db_path
    db_manager.db_path = test_db_path

    # Ensure data directory exists
    os.makedirs(os.path.dirname(test_db_path), exist_ok=True)

    # Run database initialization
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(db_manager.initialize())
    finally:
        loop.close()

    yield

    # Cleanup: Close all DB connections to avoid hangs
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(db_manager.close_all())
    finally:
        loop.close()

    # Cleanup after all tests
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        # Also cleanup WAL files if they exist
        for suffix in ["-shm", "-wal"]:
            if os.path.exists(test_db_path + suffix):
                os.remove(test_db_path + suffix)

@pytest.fixture(scope="session", autouse=True)
def global_cleanup():
    """
    Ensures that all background tasks are cancelled at the end of the test session.
    """
    yield
    # Final cleanup of any dangling async tasks
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            for task in asyncio.all_tasks(loop):
                task.cancel()
    except Exception:
        pass

@pytest.fixture(autouse=True)
def cleanup_sys_modules():
    """
    Safety net: remove any MagicMock left in sys.modules after a test.
    This prevents state pollution between test modules.
    """
    yield
    import sys
    from unittest.mock import MagicMock
    for name in list(sys.modules.keys()):
        try:
            if isinstance(sys.modules.get(name), MagicMock):
                del sys.modules[name]
        except (ImportError, AttributeError):
            pass
