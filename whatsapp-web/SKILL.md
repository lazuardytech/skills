---
name: whatsapp-web
description: WhatsApp Web automation via Playwright and Chrome CDP. Use when the user needs to verify phone numbers on WhatsApp, send WhatsApp messages, read chat history, check if a number is registered on WhatsApp, automate WhatsApp Web login, or perform bulk number verification. Triggers include requests to "check this number on WhatsApp", "send a WhatsApp message", "verify WhatsApp numbers", "read WhatsApp messages", "open WhatsApp chat", "batch check numbers", or any task requiring programmatic WhatsApp Web interaction.
license: Proprietary
compatibility: Requires Python 3.10+, Google Chrome, and Playwright. macOS or Linux only.
metadata:
  author: lazuardy-tech
  version: "1.0"
---

# whatsapp-web

Python package for automating WhatsApp Web via Playwright + Chrome DevTools Protocol (CDP).

## Setup

1. Install dependencies:
   ```bash
   pip install playwright>=1.58.0
   ```

2. First-time login — start Chrome manually, scan QR code once:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --user-data-dir=~/chrome_profile \
     --remote-debugging-port=9222
   ```
   Then open https://web.whatsapp.com and scan QR from phone. Session persists in `chrome_profile/`.

## Usage

```python
import asyncio
from src import WhatsAppWeb

async def main():
    async with WhatsAppWeb() as wa:
        # Check if number is on WhatsApp
        result = await wa.check_number("081234567890")

        # Send a message
        await wa.send_message("Ezra", "Hello!")

        # Batch check numbers
        results = await wa.check_numbers(["08111", "08222", "08333"])

asyncio.run(main())
```

### Handle QR code login

```python
from src import WhatsAppWeb, LoginRequiredError

wa = WhatsAppWeb()
try:
    await wa.start()
except LoginRequiredError:
    print("Scan QR code on your phone...")
    await wa.wait_for_login(timeout=120)
```

## API

| Method | Description |
|--------|-------------|
| `start()` | Launch Chrome, connect, navigate to WA Web |
| `stop()` | Disconnect (Chrome keeps running) |
| `check_number(phone)` | Check if number is on WhatsApp → `bool` |
| `check_numbers(phones)` | Batch check → `dict[str, bool]` |
| `send_message(to, message)` | Send message to contact |
| `open_chat(name_or_number)` | Open chat window |
| `read_last_messages(count)` | Read last N messages from open chat |
| `is_logged_in()` | Check login state → `bool` |
| `wait_for_login(timeout)` | Wait for QR scan → `bool` |

## Configuration

```python
WhatsAppWeb(
    chrome_profile_dir="/path/to/profile",  # Default: ~/projects/lt/leads/chrome_profile
    cdp_port=9222,                          # CDP port
    chrome_path="/usr/bin/chrome",           # Auto-detected on macOS/Linux
    between_delay=3.0,                      # Anti-ban delay (seconds)
)
```

## Exceptions

| Exception | When |
|-----------|------|
| `LoginRequiredError` | QR code scan needed |
| `ChatNotFoundError` | Contact/number not found |
| `BrowserNotRunningError` | Chrome not reachable |
| `BrowserLaunchError` | Failed to start Chrome |

## Important notes

- Chrome persists across runs — never killed by the skill
- Anti-ban delay (default 3s) between operations
- Phone formatting defaults to Indonesian numbers (+62)
- All interactions are keyboard/text-based (no CSS selectors) for resilience against WA Web DOM changes
- Number verification checks multiple phone format variants for accuracy
