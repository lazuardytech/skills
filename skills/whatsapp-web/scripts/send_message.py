#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Send a WhatsApp message to a contact.

Usage:
    python3 scripts/send_message.py --to "Ezra" --message "Hello!"
    python3 scripts/send_message.py --to 081234567890 --message "Hi there"
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(to: str, message: str) -> dict:
    from src import WhatsAppWeb, LoginRequiredError, ChatNotFoundError

    try:
        async with WhatsAppWeb() as wa:
            await wa.send_message(to, message)
            return {"status": "sent", "to": to}
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)
    except ChatNotFoundError:
        print(f"Couldn't find a contact named {to!r}.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a WhatsApp message")
    parser.add_argument("--to", required=True, help="Contact name or phone number")
    parser.add_argument("--message", required=True, help="Message text to send")
    args = parser.parse_args()

    result = asyncio.run(main(args.to, args.message))
    print(json.dumps(result, indent=2))
