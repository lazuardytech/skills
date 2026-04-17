#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Check if phone number(s) are registered on WhatsApp.

Usage:
    python3 scripts/check_number.py --phone 081234567890
    python3 scripts/check_number.py --phones 08111,08222,08333
"""

import argparse
import asyncio
import json
import os
import sys

# Add skill root to path so `from src import ...` works
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(phones: list[str]) -> dict[str, bool]:
    from src import WhatsAppWeb, LoginRequiredError

    try:
        async with WhatsAppWeb() as wa:
            results = await wa.check_numbers(phones)
            return results
    except LoginRequiredError:
        print("ERROR: WhatsApp Web requires QR code login.", file=sys.stderr)
        print("Run: python3 scripts/login.py --wait", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if phone numbers are on WhatsApp")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--phone", help="Single phone number to check")
    group.add_argument("--phones", help="Comma-separated phone numbers to check")
    args = parser.parse_args()

    phones = [args.phone] if args.phone else [p.strip() for p in args.phones.split(",")]
    results = asyncio.run(main(phones))
    print(json.dumps(results, indent=2))
