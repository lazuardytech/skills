#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Launch WhatsApp Web, poll login state every 5s until user is logged in.

Opens Chrome with persistent profile and navigates to web.whatsapp.com.
Prints progress to stderr. Exits with code 0 when logged in.

Usage:
    python3 scripts/login.py                    # Wait up to 300s (default)
    python3 scripts/login.py --timeout 120      # Custom timeout
    python3 scripts/login.py --check            # Check current state only, no waiting
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

POLL_INTERVAL = 5


async def run(timeout: int, check_only: bool) -> dict:
    from src import WhatsAppWeb
    from src.session import WhatsAppSession
    from playwright.async_api import async_playwright

    wa = WhatsAppWeb()

    print("Starting Chrome...", file=sys.stderr)
    wa._chrome.ensure_running()

    wa._pw_cm = async_playwright()
    wa._playwright = await wa._pw_cm.__aenter__()
    wa._browser, wa._context, wa._page = await wa._chrome.connect(wa._playwright)
    wa._session = WhatsAppSession(wa._page)

    print("Navigating to web.whatsapp.com...", file=sys.stderr)
    await wa._session.navigate()

    elapsed = 0
    while True:
        state = await wa._session.get_login_state()

        if state == "logged_in":
            print("Logged in. WhatsApp Web is ready.", file=sys.stderr)
            await wa.stop()
            return {"state": "logged_in"}

        if check_only:
            await wa.stop()
            return {"state": state, "action": "Scan QR code from your phone" if state == "qr_code" else None}

        if elapsed >= timeout:
            await wa.stop()
            return {"state": "timeout", "error": f"Login timed out after {timeout}s"}

        if state == "qr_code":
            print(f"[{elapsed}s/{timeout}s] Waiting for QR code scan...", file=sys.stderr)
        elif state == "loading":
            print(f"[{elapsed}s/{timeout}s] WhatsApp Web loading...", file=sys.stderr)
        else:
            print(f"[{elapsed}s/{timeout}s] State: {state}", file=sys.stderr)

        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch WA Web and wait for login")
    parser.add_argument("--timeout", type=int, default=300, help="Max wait time in seconds (default: 300)")
    parser.add_argument("--check", action="store_true", help="Check current state only, don't wait")
    args = parser.parse_args()

    result = asyncio.run(run(args.timeout, args.check))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["state"] == "logged_in" else 1)
