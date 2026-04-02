import asyncio
import logging
import sys
import os

# Setup logging to stdout
logging.basicConfig(level=logging.ERROR, stream=sys.stdout)

async def test():
    try:
        # Load environment variables (done by config which is imported by repo)
        from repositories.user_repository import user_repo
        
        print("Testing get_all_levels...")
        levels = await user_repo.get_all_levels()
        print(f"Levels found: {len(levels)}")
        for l in levels:
            print(f" - {l['name']}")
            
        print("\nTesting list_users...")
        users = await user_repo.list_users(limit=10)
        print(f"Users found: {len(users)}")
        for u in users:
            print(f" - {u['username']} (Role: {u['role']})")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
