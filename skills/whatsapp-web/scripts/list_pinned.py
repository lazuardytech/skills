#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""List pinned chats from the WhatsApp Web sidebar (max 3).

Usage:
    python3 scripts/list_pinned.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main() -> dict:
    from src import LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            pinned = await wa.list_pinned_chats()
            return {"count": len(pinned), "chats": pinned}
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    result = asyncio.run(main())
    print(json.dumps(result, indent=2, ensure_ascii=False))
