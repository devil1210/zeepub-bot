import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.curdir))

from services.ai.semantic_service import semantic_service

async def test_semantic():
    print("Testing SemanticService...")
    semantic_service.setup_flows()
    stats = semantic_service.update_index()
    print(f"Index Update Stats: {stats}")
    
    # Query test
    query = "busco algo sobre reencarnación"
    print(f"Querying: '{query}'")
    results = semantic_service.search(query)
    print(f"Results: {results}")

if __name__ == "__main__":
    asyncio.run(test_semantic())
