import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import config
from supabase_client import get_supabase_client

async def wipe_supabase_tables():
    client = get_supabase_client()
    if not client:
        print("No supabase client")
        return

    print("Deleting all from local_books...")
    res = client.table("local_books").delete().neq("id", -1).execute()
    print("Deleted local_books")
    
    print("Deleting all from translators_groups...")
    res = client.table("translators_groups").delete().neq("id", -1).execute()
    print("Deleted translators_groups")
    
    print("Deleting all from library_sources...")
    res = client.table("library_sources").delete().neq("id", -1).execute()
    print("Deleted library_sources")

if __name__ == "__main__":
    asyncio.run(wipe_supabase_tables())
