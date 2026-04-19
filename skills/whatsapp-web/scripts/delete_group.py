#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Delete a WhatsApp group: kick all members, exit, delete from chat list.

Usage:
    python3 scripts/delete_group.py --name "LT Marketing Team" --confirm

This is DESTRUCTIVE — the --confirm flag is required. The agent must ask
the user "are you sure?" and relay the confirmation before invoking this
script with --confirm.

Works best when the caller is a group admin (only admins can remove other
members). If the caller isn't admin, kicking is skipped silently and the
script falls through to Exit + Delete (same effect as leaving + hiding
the group from your chat list).
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
            return await wa.delete_group(name_or_number)
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)
    except ChatNotFoundError:
        print(f"Couldn't find a group named {name_or_number!r}.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete a WhatsApp group")
    parser.add_argument(
        "--name",
        dest="name_or_number",
        required=True,
        help="Group name (as shown in the chat list)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required to actually delete. Without this flag the script refuses to run.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "Refusing to run without --confirm. This action kicks all members, "
            "exits the group, and removes it from the chat list.",
            file=sys.stderr,
        )
        sys.exit(3)

    result = asyncio.run(main(args.name_or_number))
    print(json.dumps(result, indent=2, ensure_ascii=False))
