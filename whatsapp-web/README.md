# WhatsApp Web Skill

A reusable Python package for automating WhatsApp Web via Playwright + Chrome DevTools Protocol (CDP).

## Capabilities

- **Login management** — Detect QR code screen, wait for login, check session state
- **Number verification** — Check if a phone number is registered on WhatsApp
- **Chat** — Open conversations, send messages, read last messages
- **Browser lifecycle** — Launch/connect to Chrome with persistent profile

## Setup

### Requirements

- Python 3.10+
- Google Chrome installed
- Playwright (`pip install playwright`)

### First-time login

1. Run Chrome with the profile:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --user-data-dir=~/projects/lt/leads/chrome_profile \
     --remote-debugging-port=9222
   ```
2. Navigate to https://web.whatsapp.com in Chrome
3. Scan the QR code from your phone
4. The session is saved in `chrome_profile/` — no need to re-scan next time

## Usage

```python
import asyncio
from src import WhatsAppWeb

async def main():
    async with WhatsAppWeb() as wa:
        # Check if a number is on WhatsApp
        on_wa = await wa.check_number("081234567890")
        print(f"On WhatsApp: {on_wa}")

        # Send a message
        await wa.send_message("Ezra", "Hello from the agent!")

        # Batch check numbers
        results = await wa.check_numbers(["08111", "08222", "08333"])
        print(results)

asyncio.run(main())
```

### Handling QR code login

```python
from src import WhatsAppWeb, LoginRequiredError

wa = WhatsAppWeb()
try:
    await wa.start()
except LoginRequiredError:
    print("Please scan the QR code on your phone...")
    await wa.wait_for_login(timeout=120)
```

## Package Structure

```
src/
├── __init__.py      # WhatsAppWeb facade class
├── browser.py       # Chrome lifecycle + CDP connection
├── session.py       # Login detection & navigation
├── chat.py          # Send/read messages
├── contacts.py      # Contact search & number verification
├── phone.py         # Phone number formatting utilities
└── errors.py        # Custom exceptions
```

## API Reference

### `WhatsAppWeb(chrome_profile_dir, cdp_port, chrome_path, between_delay)`

| Method | Description |
|--------|-------------|
| `start()` | Launch Chrome, connect, navigate to WA Web |
| `stop()` | Disconnect (Chrome keeps running) |
| `check_number(phone)` | Check if number is on WhatsApp → `bool` |
| `check_numbers(phones)` | Batch check → `dict[str, bool]` |
| `send_message(to, message)` | Send a message to a contact |
| `open_chat(name_or_number)` | Open a chat window |
| `read_last_messages(count)` | Read last N messages from open chat |
| `is_logged_in()` | Check login state → `bool` |
| `wait_for_login(timeout)` | Wait for QR scan → `bool` |

### Exceptions

| Exception | When |
|-----------|------|
| `LoginRequiredError` | QR code scan needed |
| `ChatNotFoundError` | Contact/number not found |
| `BrowserNotRunningError` | Chrome not reachable on CDP port |
| `BrowserLaunchError` | Failed to start Chrome |

## Notes

- Chrome is never killed by the skill — it persists across runs to keep the WA session alive
- Anti-ban: configurable delay between operations (default 3s)
- Phone formatting defaults to Indonesian numbers (+62), configurable via `country_code` parameter
- All interactions are keyboard/text-based (no CSS selectors) for resilience against WA Web DOM changes
