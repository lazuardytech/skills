#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Check WhatsApp Web login state or wait for QR code scan.

Usage:
    python3 scripts/login.py                  # Check current state
    python3 scripts/login.py --wait           # Wait for QR scan (default 120s)
    python3 scripts/login.py --wait --timeout 60
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def check_state() -> dict:
    from src import WhatsAppWeb, LoginRequiredError

    wa = WhatsAppWeb()
    try:
        await wa.start()
        return {"state": "logged_in"}
    except LoginRequiredError:
        return {"state": "qr_code", "action": "Scan QR code from your phone"}
    finally:
        await wa.stop()


async def wait_for_login(timeout: int) -> dict:
    from src import WhatsAppWeb, LoginRequiredError
    from src.session import WhatsAppSession
    from playwright.async_api import async_playwright

    wa = WhatsAppWeb()
    wa._chrome.ensure_running()

    wa._playwright = await async_playwright().__aenter__()
    wa._browser, wa._context, wa._page = await wa._chrome.connect(wa._playwright)

    wa._session = WhatsAppSession(wa._page)
    await wa._session.navigate()

    state = await wa._session.get_login_state()
    if state == "logged_in":
        await wa.stop()
        return {"state": "logged_in"}

    print("Waiting for QR code scan...", file=sys.stderr)
    try:
        await wa._session.wait_for_login(timeout)
        await wa.stop()
        return {"state": "logged_in"}
    except LoginRequiredError:
        await wa.stop()
        return {"state": "timeout", "error": f"Login timed out after {timeout}s"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check or wait for WhatsApp Web login")
    parser.add_argument("--wait", action="store_true", help="Wait for QR code scan")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds (default: 120)")
    args = parser.parse_args()

    if args.wait:
        result = asyncio.run(wait_for_login(args.timeout))
    else:
        result = asyncio.run(check_state())

    print(json.dumps(result, indent=2))
