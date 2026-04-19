#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Pin or unpin a WhatsApp chat in the sidebar.

Usage:
    python3 scripts/pin_chat.py --to "Ezra"
    python3 scripts/pin_chat.py --to "Ezra" --unpin
    python3 scripts/pin_chat.py --to 081234567890

WhatsApp Web allows at most 3 pinned chats.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(name_or_number: str, unpin: bool) -> dict:
    from src import ChatNotFoundError, LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            if unpin:
                return await wa.unpin_chat(name_or_number)
            return await wa.pin_chat(name_or_number)
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)
    except ChatNotFoundError:
        print(f"Couldn't find a contact named {name_or_number!r}.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pin or unpin a WhatsApp chat")
    parser.add_argument(
        "--to",
        dest="name_or_number",
        required=True,
        help="Contact name or phone number",
    )
    parser.add_argument(
        "--unpin",
        action="store_true",
        help="Unpin the chat instead of pinning",
    )
    args = parser.parse_args()

    result = asyncio.run(main(args.name_or_number, args.unpin))
    print(json.dumps(result, indent=2, ensure_ascii=False))
