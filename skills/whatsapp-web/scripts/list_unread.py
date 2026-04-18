#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""List chats with unread messages from the WhatsApp Web sidebar.

Usage:
    python3 scripts/list_unread.py                   # scan top 50 chats
    python3 scripts/list_unread.py --limit 100       # scan deeper
    python3 scripts/list_unread.py --count-only      # just the totals
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(limit: int, count_only: bool) -> dict:
    from src import LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            summary = await wa.unread_summary(limit=limit)
            if count_only:
                return {
                    "chat_count": summary["chat_count"],
                    "message_count": summary["message_count"],
                }
            return summary
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List unread chats in the WhatsApp Web sidebar")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="How many sidebar rows to scan, from the top (default: 50)",
    )
    parser.add_argument(
        "--count-only",
        action="store_true",
        help="Return only chat_count and message_count",
    )
    args = parser.parse_args()

    result = asyncio.run(main(args.limit, args.count_only))
    print(json.dumps(result, indent=2, ensure_ascii=False))
