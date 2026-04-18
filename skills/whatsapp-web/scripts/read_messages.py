#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Read the most recent messages from a WhatsApp chat.

Usage:
    python3 scripts/read_messages.py --from "Ezra"
    python3 scripts/read_messages.py --from 081234567890 --count 20
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(name_or_number: str, count: int) -> dict:
    from src import ChatNotFoundError, LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            await wa.open_chat(name_or_number)
            messages = await wa.read_last_messages(count)
            return {
                "from": name_or_number,
                "count": len(messages),
                "messages": messages,
            }
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)
    except ChatNotFoundError:
        print(f"Couldn't find a contact named {name_or_number!r}.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read recent WhatsApp messages from a chat")
    parser.add_argument(
        "--from",
        dest="name_or_number",
        required=True,
        help="Contact name or phone number",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="How many recent messages to read (default: 10)",
    )
    args = parser.parse_args()

    result = asyncio.run(main(args.name_or_number, args.count))
    print(json.dumps(result, indent=2, ensure_ascii=False))
