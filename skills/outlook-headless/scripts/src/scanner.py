import asyncio
import json
import sys

try:
    from .outlook_client import OutlookClient, SearchCriteria
except ImportError:
    from outlook_client import OutlookClient, SearchCriteria

async def main():
    if len(sys.argv) < 2:
        print("Usage: python scanner.py '<query>' [limit]")
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    criteria = SearchCriteria(query=query)
    
    async with OutlookClient(headless=True) as client:
        results = await client.search(criteria, limit=limit)
        output = [r.model_dump() for r in results]
        print(json.dumps(output, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
