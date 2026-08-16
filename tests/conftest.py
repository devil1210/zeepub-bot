"""
Pytest configuration file.
Adds the project root to sys.path so tests can import project modules.
"""

import asyncio
import sys
from pathlib import Path

import pytest

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
    Uses PostgreSQL as configured in config.
    """
    from core.db_manager_pg import pg_manager

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(pg_manager.initialize())
    except Exception:
        pass
    finally:
        loop.close()

    yield

    # Cleanup: Close all DB connections
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(pg_manager.close())
    except Exception:
        pass
    finally:
        loop.close()


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
