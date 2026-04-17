---
name: whatsapp-web
description: WhatsApp Web automation via Playwright and Chrome CDP. Use when the user needs to open WhatsApp Web, launch the WhatsApp Web browser, verify phone numbers on WhatsApp, send WhatsApp messages, read chat history, check if a number is registered on WhatsApp, automate WhatsApp Web login, or perform bulk number verification. Triggers include requests to "open WhatsApp Web", "buka WhatsApp Web", "launch WhatsApp", "check this number on WhatsApp", "send a WhatsApp message", "verify WhatsApp numbers", "read WhatsApp messages", "open WhatsApp chat", "batch check numbers", or any task requiring programmatic WhatsApp Web interaction. For any "open/launch/buka WhatsApp Web" request, run `scripts/login.py` — it starts Chrome, navigates to web.whatsapp.com, and waits for QR scan if needed.
license: Proprietary
compatibility: Requires Python 3.10+, Google Chrome, and Playwright. macOS or Linux only.
metadata:
  author: lazuardy-tech
  version: "1.0"
---

# whatsapp-web

WhatsApp Web automation via Playwright + Chrome CDP. Scripts output JSON to stdout.

## Setup

Requires Python 3.10+, Google Chrome, and Playwright.

First-time login — scan QR code once:

```bash
python3 scripts/login.py
```

This opens Chrome, navigates to web.whatsapp.com, and polls every 5s until user is logged in. Script exits with code 0 when login detected. Chrome profile persists in `/tmp/whatsapp-web/chrome_profile/`. No re-scan needed after first login.

## Available Scripts

### Check if number(s) are on WhatsApp

```bash
# Single number
python3 scripts/check_number.py --phone 081234567890

# Multiple numbers (comma-separated)
python3 scripts/check_number.py --phones 08111,08222,08333
```

Output: `{"081234567890": true}`

### Send a message

```bash
python3 scripts/send_message.py --to "Ezra" --message "Hello!"
python3 scripts/send_message.py --to 081234567890 --message "Hi there"
```

Output: `{"status": "sent", "to": "Ezra"}`

### Login / wait for QR scan

```bash
# Launch Chrome and wait until logged in (polls every 5s, default timeout 300s)
python3 scripts/login.py

# Custom timeout
python3 scripts/login.py --timeout 120

# Check state only, don't wait
python3 scripts/login.py --check
```

Exits code 0 when logged in, 1 on timeout. Progress printed to stderr.

Output: `{"state": "logged_in"}` or `{"state": "timeout", "error": "..."}`

## Script conventions

- All scripts output JSON to stdout, diagnostics to stderr
- Exit code 0 = success, 1 = login required, 2 = contact not found
- Run `python3 scripts/<name>.py --help` for usage
- Scripts use PEP 723 inline dependencies — run with `uv run` or install Playwright manually

## Important notes

- Chrome persists across runs — never killed by the skill
- Anti-ban delay (default 3s) between operations
- Phone formatting defaults to Indonesian numbers (+62)
- All interactions are keyboard/text-based (no CSS selectors) for resilience against WA Web DOM changes
- Number verification checks multiple phone format variants for accuracy
