import asyncio
from core.supabase_manager import supabase_manager
from config.config_settings import config

async def test_supabase():
    print(f"Supabase URL: {config.SUPABASE_URL}")
    print(f"Supabase Service Role Key: {config.SUPABASE_SERVICE_ROLE_KEY[:20]}...")
    
    client = supabase_manager.get_client()
    try:
        print("Fetching user_levels...")
        res = client.table('user_levels').select("*").execute()
        print(f"Status: OK, Data size: {len(res.data)}")
        for r in res.data:
            print(f" - {r['name']} (ID: {r['id']})")
            
        print("\nFetching users...")
        res = client.table('users').select("*").execute()
        print(f"Status: OK, Data size: {len(res.data)}")
        
        print("\nFetching users with join...")
        res = client.table('users').select("*, level:user_levels(name, color, daily_downloads)").execute()
        print(f"Status: OK, Data size: {len(res.data)}")
        if res.data:
            print(f" - First user level: {res.data[0].get('level')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_supabase())
