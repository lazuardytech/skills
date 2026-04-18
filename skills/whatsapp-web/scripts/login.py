#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Open WhatsApp Web and report the current login state.

By default this script returns immediately after opening the window —
it does NOT block waiting for a QR scan, so the calling agent stays
responsive. Pass --wait to poll until the user finishes signing in.

Usage:
    python3 scripts/login.py                # Open WA Web, report state, exit
    python3 scripts/login.py --wait         # Block until logged in (max 300s)
    python3 scripts/login.py --wait --timeout 120
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

POLL_INTERVAL = 5


async def run(wait: bool, timeout: int) -> dict:
    from playwright.async_api import async_playwright
    from src import WhatsAppWeb
    from src.session import WhatsAppSession

    wa = WhatsAppWeb()

    print("Opening WhatsApp Web...", file=sys.stderr)
    wa._chrome.ensure_running()

    wa._pw_cm = async_playwright()
    wa._playwright = await wa._pw_cm.__aenter__()
    wa._browser, wa._context, wa._page = await wa._chrome.connect(wa._playwright)
    wa._session = WhatsAppSession(wa._page)

    await wa._session.navigate()

    # First state read.
    state = await wa._session.get_login_state()

    if state == "logged_in":
        print("WhatsApp Web is ready.", file=sys.stderr)
        await wa.stop()
        return {"state": "logged_in"}

    # Non-blocking mode: report state and exit so the agent stays responsive.
    if not wait:
        await wa.stop()
        action = None
        message = None
        if state == "qr_code":
            action = "Scan the QR code with your phone"
            message = (
                "WhatsApp Web is open. Please scan the QR code with your phone, then try again."
            )
        elif state == "loading":
            message = "WhatsApp Web is still loading. Please try again in a few seconds."
        else:
            message = "WhatsApp Web is open but not signed in yet."
        return {"state": state, "action": action, "message": message}

    # Blocking mode: poll until logged in or timeout.
    elapsed = 0
    while True:
        if state == "logged_in":
            print("WhatsApp Web is ready.", file=sys.stderr)
            await wa.stop()
            return {"state": "logged_in"}

        if elapsed >= timeout:
            await wa.stop()
            return {
                "state": "timeout",
                "error": f"Login didn't complete within {timeout}s",
            }

        if state == "qr_code":
            print(
                f"Please scan the QR code with your phone... ({elapsed}s/{timeout}s)",
                file=sys.stderr,
            )
        elif state == "loading":
            print(f"Getting things ready... ({elapsed}s/{timeout}s)", file=sys.stderr)
        else:
            print(f"Still waiting... ({elapsed}s/{timeout}s)", file=sys.stderr)

        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        state = await wa._session.get_login_state()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open WhatsApp Web and report login state")
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Block until the user finishes signing in (default: exit immediately)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="With --wait: max seconds to wait for login (default: 300)",
    )
    args = parser.parse_args()

    result = asyncio.run(run(args.wait, args.timeout))
    print(json.dumps(result, indent=2))
    # Exit 0 on logged_in OR non-blocking open (success). 1 only on --wait timeout.
    sys.exit(1 if result["state"] == "timeout" else 0)
