#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Add a new WhatsApp contact via the New Chat → New contact dialog.

Usage:
    python3 scripts/add_contact.py --phone 081234567890 --first-name Ezra
    python3 scripts/add_contact.py --phone 081234567890 --first-name Ezra \
        --last-name Wijaya --sync

The agent should ask the user for First Name, Last Name, and whether to
sync the contact to their phone before invoking this script.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(phone: str, first_name: str, last_name: str, sync_to_phone: bool) -> dict:
    from src import LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            return await wa.add_contact(
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                sync_to_phone=sync_to_phone,
            )
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new WhatsApp contact")
    parser.add_argument("--phone", required=True, help="Phone number (digits, +62 or local format)")
    parser.add_argument("--first-name", required=True, help="Contact first name")
    parser.add_argument("--last-name", default="", help="Contact last name (optional)")
    parser.add_argument(
        "--sync",
        dest="sync_to_phone",
        action="store_true",
        help="Sync this contact to the phone's address book",
    )
    args = parser.parse_args()

    result = asyncio.run(main(args.phone, args.first_name, args.last_name, args.sync_to_phone))
    print(json.dumps(result, indent=2, ensure_ascii=False))
