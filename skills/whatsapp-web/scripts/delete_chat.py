#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Delete a chat from the WhatsApp Web sidebar (caller-side only).

Usage:
    python3 scripts/delete_chat.py --to "Ezra" --confirm
    python3 scripts/delete_chat.py --to 081234567890 --confirm

The chat is removed from your sidebar and the message history is cleared
on your side. The other party still sees the conversation on theirs.

For active groups, exit first via scripts/exit_group.py — WA Web won't
offer "Delete chat" on a group you're still a member of.

The --confirm flag is required. Agent must ask the user for explicit
confirmation before invoking this script with --confirm. Deleting a chat
is NOT reversible.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(name_or_number: str) -> dict:
    from src import ChatNotFoundError, LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            return await wa.delete_chat(name_or_number)
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)
    except ChatNotFoundError:
        print(f"Couldn't find a chat with {name_or_number!r}.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete a WhatsApp chat from the sidebar")
    parser.add_argument(
        "--to",
        dest="name_or_number",
        required=True,
        help="Contact name, group name, or phone number",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required to actually delete. Without this flag the script refuses to run.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "Refusing to run without --confirm. Deleting a chat is not reversible.",
            file=sys.stderr,
        )
        sys.exit(3)

    result = asyncio.run(main(args.name_or_number))
    print(json.dumps(result, indent=2, ensure_ascii=False))
