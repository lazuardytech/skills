#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""List chats from the WhatsApp Web sidebar (up to 50 by default).

Usage:
    python3 scripts/list_chats.py               # top 50 chats
    python3 scripts/list_chats.py --limit 20    # top 20 chats
    python3 scripts/list_chats.py --names-only  # only names, no previews
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(limit: int, names_only: bool) -> dict:
    from src import LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            total = await wa.chat_list_total_count()
            chats = await wa.list_chats(limit=limit)
            if names_only:
                chats = [{"name": c["name"], "pinned": c["pinned"]} for c in chats]
            return {
                "total_in_sidebar": total,
                "returned": len(chats),
                "chats": chats,
            }
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List chats from the WhatsApp Web sidebar")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="How many chats to return, starting from the top (default: 50, max useful ~50)",
    )
    parser.add_argument(
        "--names-only",
        action="store_true",
        help="Return only name + pinned flag, drop message previews",
    )
    args = parser.parse_args()

    result = asyncio.run(main(args.limit, args.names_only))
    print(json.dumps(result, indent=2, ensure_ascii=False))
