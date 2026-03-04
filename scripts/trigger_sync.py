import asyncio

from core.optimized_sync_engine import optimized_sync_engine


async def trigger():
    print("🚀 Triggering bidirectional sync (Cloud -> Local)...")
    await optimized_sync_engine.force_sync_all()
    print("✅ Sync completed.")


if __name__ == "__main__":
    asyncio.run(trigger())
