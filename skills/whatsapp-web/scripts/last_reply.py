#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Return the last reply from a WhatsApp chat.

Usage:
    python3 scripts/last_reply.py --from "Ezra"
    python3 scripts/last_reply.py --from "Ezra" --any-direction
    python3 scripts/last_reply.py --from 081234567890

By default, returns the last *incoming* message (what the contact said).
Pass --any-direction to return the last message regardless of who sent it.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(name_or_number: str, any_direction: bool) -> dict:
    from src import ChatNotFoundError, LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            if any_direction:
                msg = await wa.last_message(name_or_number)
            else:
                msg = await wa.last_incoming_message(name_or_number)
            return {
                "from": name_or_number,
                "mode": "any" if any_direction else "incoming",
                "message": msg,
            }
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)
    except ChatNotFoundError:
        print(f"Couldn't find a contact named {name_or_number!r}.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get the last reply from a WhatsApp chat")
    parser.add_argument(
        "--from",
        dest="name_or_number",
        required=True,
        help="Contact name or phone number",
    )
    parser.add_argument(
        "--any-direction",
        action="store_true",
        help="Return last message regardless of sender (default: last incoming only)",
    )
    args = parser.parse_args()

    result = asyncio.run(main(args.name_or_number, args.any_direction))
    print(json.dumps(result, indent=2, ensure_ascii=False))
