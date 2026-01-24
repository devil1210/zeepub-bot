import os

from config.config_settings import BotConfig


def test_postgres_plugin_disabled():
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
    os.environ["ENABLE_POSTGRES_PLUGIN"] = "False"

    # Forzamos False por si el entorno dice lo contrario
    cfg = BotConfig(ENABLE_POSTGRES_PLUGIN=False)
    cfg.__post_init__()

    print(f"Disabled -> DATABASE_URL: '{cfg.DATABASE_URL}' (Expected: '')")
    assert cfg.DATABASE_URL == ""


def test_postgres_plugin_enabled():
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
    os.environ["ENABLE_POSTGRES_PLUGIN"] = "True"

    # En la app real, el default se lee al inicio. En test, lo pasamos explícito
    # para validar la lógica de __post_init__
    cfg = BotConfig(ENABLE_POSTGRES_PLUGIN=True)
    cfg.__post_init__()

    print(
        f"Enabled -> DATABASE_URL: '{cfg.DATABASE_URL}' (Expected: 'postgresql://...')"
    )
    assert cfg.DATABASE_URL == "postgresql://user:pass@localhost/db"


if __name__ == "__main__":
    try:
        test_postgres_plugin_disabled()
        test_postgres_plugin_enabled()
        print("✅ Config tests passed!")
    except AssertionError as e:
        print(f"❌ Config tests failed: {e}")
        exit(1)
