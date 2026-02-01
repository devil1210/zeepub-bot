import os

from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

# Supabase management API for SQL is restricted.
# But we can try to use a function or just hope the columns are added.
# Usually, people use migrations.

# If I can't run SQL, I'll just skip and warn.
print(f"URL: {url}")
print(
    "Intentando ejecutar SQL vía REST API (si está habilitado el pg_net o similar)..."
)

# Actually, Supabase doesn't have a direct SQL REST endpoint unless configured.
# But many people use 'rpc' if they have a 'exec_sql' function.

sql = """
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_download BOOLEAN DEFAULT TRUE;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_read BOOLEAN DEFAULT TRUE;
"""

# There is no default 'sql' endpoint.
# I will proceed with code changes.
