import argparse
import asyncio
import json
import sys

try:
    from .outlook_client import OutlookClient, SearchCriteria
except ImportError:
    from outlook_client import OutlookClient, SearchCriteria

async def main():
    parser = argparse.ArgumentParser(description="Outlook Headless Scanner")
    parser.add_argument("query", nargs="?", help="General search query")
    parser.add_argument("--from", dest="sender", help="Filter by sender")
    parser.add_argument("--to", help="Filter by recipient")
    parser.add_argument("--subject", help="Filter by subject")
    parser.add_argument("--after", help="Received after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Received before date (YYYY-MM-DD)")
    parser.add_argument("--unread", action="store_true", help="Unread only")
    parser.add_argument("--folder", help="Search in specific folder (e.g. 'Deleted Items')")
    parser.add_argument("--importance", help="Search by importance (e.g. 'high')")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of messages")
    parser.add_argument("--list-only", action="store_true", help="Only list headers (fast)")
    parser.add_argument("--raw", action="store_true", help="Dump raw text of the entire reading pane (fastest for threads)")
    parser.add_argument("--download-images", action="store_true", help="Download images from emails")
    parser.add_argument("--show-ui", action="store_true", help="Show browser UI")

    args = parser.parse_args()

    criteria = SearchCriteria(
        query=args.query,
        from_sender=args.sender,
        to_recipient=args.to,
        subject=args.subject,
        after=args.after,
        before=args.before,
        unread_only=args.unread,
        folder=args.folder,
        importance=args.importance
    )

    async with OutlookClient(headless=not args.show_ui) as client:
        results = await client.search(
            criteria, 
            limit=args.limit, 
            list_only=args.list_only, 
            raw=args.raw,
            download_images=args.download_images
        )
        
        # Output as JSON
        output = [r.model_dump() for r in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
