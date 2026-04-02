import asyncio
import os
from supabase import create_client

from dotenv import load_dotenv

load_dotenv()

async def wipe_supabase_tables():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Falta SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el entorno.")
        return

    print("Conectando a supabase REST...")
    client = create_client(url, key)

    print("Deleting all from local_books...")
    try:
        client.table("local_books").delete().neq("id", -1).execute()
        print("Deleted local_books")
    except Exception as e:
        print(e)
    
    print("Deleting all from translators_groups...")
    try:
        client.table("translators_groups").delete().neq("id", -1).execute()
        print("Deleted translators_groups")
    except Exception as e:
        print(e)
    
    print("Deleting all from library_sources...")
    try:
        client.table("library_sources").delete().neq("id", -1).execute()
        print("Deleted library_sources")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(wipe_supabase_tables())
