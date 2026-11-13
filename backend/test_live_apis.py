import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.catalog_service import catalog_service

async def test_live():
    res, status = await catalog_service.search_catalog("Pride and Prejudice", limit=5)
    print(f"Provider status: {status}")
    print(f"Found {len(res)} books")
    for b in res[:3]:
        print(f" - {b['title']} by {b['author']} (Provider: {b['source_provider']}, Cover: {b['cover_image'] is not None})")

if __name__ == "__main__":
    asyncio.run(test_live())

