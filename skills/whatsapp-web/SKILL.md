---
name: whatsapp-web
description: WhatsApp Web automation via Playwright and Chrome CDP. Use when the user needs to open WhatsApp Web, launch the WhatsApp Web browser, verify phone numbers on WhatsApp, send WhatsApp messages, read recent chat messages or chat history, list chats in the sidebar, count chats, count pinned chats, check if a number is registered on WhatsApp, automate WhatsApp Web login, or perform bulk number verification. Triggers include requests to "open WhatsApp Web", "buka WhatsApp Web", "launch WhatsApp", "check this number on WhatsApp", "send a WhatsApp message", "verify WhatsApp numbers", "read WhatsApp messages", "list WhatsApp messages", "show recent WhatsApp chat", "ambil pesan WhatsApp", "open WhatsApp chat", "batch check numbers", "list my WhatsApp chats", "ada berapa chat", "berapa pinned chat", "show pinned chats", or any task requiring programmatic WhatsApp Web interaction. For any "open/launch/buka WhatsApp Web" request, run `scripts/login.py` WITHOUT `--wait` — the script exits immediately after opening the window so the agent stays responsive. Never use `--wait` unless the user explicitly asks the agent to wait for them to sign in. For reading messages, run `scripts/read_messages.py --from <name>`. For listing chats, run `scripts/list_chats.py`. For pinned chats, run `scripts/list_pinned.py`. Always keep responses to the user friendly and non-technical (say "Opening WhatsApp Web..." instead of "Starting Chrome with CDP").
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

This opens Chrome, navigates to web.whatsapp.com, reports the current login state, and **exits immediately** so the calling agent stays responsive. If the user still needs to scan the QR code, tell them to scan it from their phone and re-run the task once signed in. Chrome profile persists in `/tmp/whatsapp-web/chrome_profile/`, so no re-scan is needed after the first login.

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

### Read recent messages from a chat

```bash
python3 scripts/read_messages.py --from "Ezra"
python3 scripts/read_messages.py --from 081234567890 --count 20
```

Output: `{"from": "Ezra", "count": 10, "messages": ["...", "..."]}`

### List chats in the sidebar

```bash
python3 scripts/list_chats.py                 # top 50 chats
python3 scripts/list_chats.py --limit 20      # top 20
python3 scripts/list_chats.py --names-only    # drop previews
```

Output: `{"total_in_sidebar": 188, "returned": 50, "chats": [{"name": "...", "preview": "...", "pinned": false}, ...]}`

`total_in_sidebar` is the full chat count WhatsApp reports (all archived + active), `returned` is how many entries the script actually collected.

### List pinned chats

```bash
python3 scripts/list_pinned.py
```

Output: `{"count": 2, "chats": [{"name": "...", "preview": "...", "pinned": true}, ...]}`

WhatsApp Web allows at most 3 pinned chats.

### Open WhatsApp Web / check login state

```bash
# Default: open WA Web, report state, exit immediately (non-blocking)
python3 scripts/login.py

# Block until the user signs in (only when explicitly requested)
python3 scripts/login.py --wait
python3 scripts/login.py --wait --timeout 120
```

Default mode exits right after opening the window — agents MUST NOT use `--wait` unless the user explicitly asks to wait for login, otherwise the agent will appear to hang while the user scans the QR code.

Output examples:
- `{"state": "logged_in"}`
- `{"state": "qr_code", "action": "Scan the QR code with your phone", "message": "..."}`
- `{"state": "timeout", "error": "..."}` (only with `--wait`)

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
