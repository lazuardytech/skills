#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Exit (leave) a WhatsApp group.

Usage:
    python3 scripts/exit_group.py --name "LT Team" --confirm

The group stays in the chat list as a read-only conversation. Use
delete_chat.py afterwards if you also want to hide it from the sidebar,
or delete_group.py for the full kick-all + exit + delete teardown.

The --confirm flag is required. Agent must ask the user for confirmation
first. Leaving is reversible only if an admin re-invites.
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
            return await wa.exit_group(name_or_number)
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)
    except ChatNotFoundError:
        print(f"Couldn't find a group named {name_or_number!r}.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exit (leave) a WhatsApp group")
    parser.add_argument(
        "--name",
        dest="name_or_number",
        required=True,
        help="Group name (as shown in the chat list)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required to actually exit. Without this flag the script refuses to run.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "Refusing to run without --confirm. Leaving a group is reversible "
            "only if an admin re-invites you.",
            file=sys.stderr,
        )
        sys.exit(3)

    result = asyncio.run(main(args.name_or_number))
    print(json.dumps(result, indent=2, ensure_ascii=False))
