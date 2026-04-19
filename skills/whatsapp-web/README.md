# WhatsApp Web Skill

WhatsApp Web automation via Playwright + Chrome DevTools Protocol (CDP). Ships CLI scripts (agent-callable) backed by a reusable Python package.

## Capabilities

- **Login management** — Open WA Web, detect QR code, check session state (non-blocking by default)
- **Number verification** — Check if a phone number is registered on WhatsApp (single or batch)
- **Messaging** — Send messages, read recent messages (structured: direction/sender/time/date/text)
- **Last reply** — Get the last reply from a specific contact ("X bales apa") or the last message in a chat
- **Chat list** — List chats, list pinned chats (max 3), list unread chats with per-chat unread counts
- **Pin / unpin** — Pin or unpin a chat via the header menu (idempotent; detects current state from the sidebar row)
- **Create group** — New Chat → New group → add members → set subject → Create; reports per-member success/failure
- **Browser lifecycle** — Launch a dedicated Chrome window with persistent profile; never hijacks the user's default Chrome; race-safe across concurrent runs via lockfile

## Setup

### Requirements

- Python 3.10+
- Google Chrome installed
- Playwright — scripts declare this inline via PEP 723, so `uv run scripts/<name>.py` works out of the box. Otherwise `pip install "playwright>=1.58.0"`.
- macOS or Linux (Chrome path auto-detected)

### First-time login

Run:

```bash
python3 scripts/login.py
```

This opens a dedicated Chrome window (separate from your default profile) navigated to `web.whatsapp.com`, reports the current login state, and exits immediately. If the output says a QR code is needed, scan it from your phone. The session persists in `/tmp/whatsapp-web/chrome_profile/`, so no re-scan after the first login.

To block until the user finishes scanning (rarely needed — only when explicitly requested):

```bash
python3 scripts/login.py --wait --timeout 120
```

## CLI Scripts (agent-callable)

All scripts print JSON to stdout and diagnostics to stderr. Exit codes: `0` success, `1` login required, `2` contact not found.

| Script | Purpose |
|--------|---------|
| `scripts/login.py` | Open WA Web, check login state. Non-blocking by default; `--wait` opts into blocking until login |
| `scripts/check_number.py` | Verify one (`--phone`) or many (`--phones a,b,c`) numbers against WhatsApp |
| `scripts/add_contact.py` | Add a new contact: `--phone --first-name [--last-name] [--sync]` |
| `scripts/send_message.py` | Send a message: `--to <name-or-number> --message "..."` |
| `scripts/pin_chat.py` | Pin or unpin a chat: `--to <name-or-number> [--unpin]` (max 3 pinned) |
| `scripts/create_group.py` | Create a group: `--name "..." --members "a,b,c"` (repeatable) |
| `scripts/read_messages.py` | Read last N messages from a chat: `--from <name-or-number> [--count 10]` |
| `scripts/last_reply.py` | Last incoming reply: `--from <name>`. Add `--any-direction` for last message regardless of sender |
| `scripts/list_chats.py` | List sidebar chats: `[--limit 50] [--names-only]` |
| `scripts/list_pinned.py` | List pinned chats (max 3) |
| `scripts/list_unread.py` | List unread chats: `[--limit 50] [--count-only]` |

### Example output shapes

`check_number.py`:
```json
{"081234567890": true}
```

`read_messages.py` / `last_reply.py` (message objects):
```json
{
  "direction": "in",
  "sender": "Ezra",
  "time": "08.42",
  "date": "17/04/2026",
  "text": "oke siap"
}
```
`direction` is `"in"` (received) or `"out"` (sent by the logged-in user).

`list_chats.py`:
```json
{
  "total_in_sidebar": 188,
  "returned": 50,
  "chats": [{"name": "...", "preview": "...", "pinned": false, "unread": false, "unread_count": 0}]
}
```

`list_unread.py`:
```json
{
  "chat_count": 3,
  "message_count": 46,
  "chats": [{"name": "LT Marketing Team", "unread_count": 33, "unread": true, "pinned": false}]
}
```

Run any script with `--help` for full flag details.

## Library Usage

```python
import asyncio
from src import WhatsAppWeb

async def main():
    async with WhatsAppWeb() as wa:
        # Number verification
        on_wa = await wa.check_number("081234567890")

        # Messaging
        await wa.send_message("Ezra", "Hello!")
        msgs = await wa.read_last_messages(count=10)

        # Last reply from a contact
        reply = await wa.last_incoming_message("Ezra")
        latest = await wa.last_message("Ezra")  # any direction

        # Chat list
        chats = await wa.list_chats(limit=50)
        pinned = await wa.list_pinned_chats()
        summary = await wa.unread_summary(limit=50)

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
skills/whatsapp-web/
├── SKILL.md            # Agent triggers + instructions
├── README.md           # This file
├── scripts/            # CLI entry points
│   ├── login.py
│   ├── check_number.py
│   ├── add_contact.py
│   ├── send_message.py
│   ├── pin_chat.py
│   ├── create_group.py
│   ├── read_messages.py
│   ├── last_reply.py
│   ├── list_chats.py
│   ├── list_pinned.py
│   └── list_unread.py
└── src/
    ├── __init__.py     # WhatsAppWeb facade class
    ├── browser.py      # Chrome lifecycle + CDP connection (lockfile-protected)
    ├── session.py      # Login detection (DOM-first) & navigation
    ├── chat.py         # Send/read messages, chat list, pinned, unread, pin/unpin
    ├── contacts.py     # Contact search, number verification, add contact
    ├── groups.py       # Group creation
    ├── phone.py        # Phone number formatting utilities
    └── errors.py       # Custom exceptions
```

## API Reference

### `WhatsAppWeb(chrome_profile_dir=None, cdp_port=9222, chrome_path=None, between_delay=3.0)`

| Method | Returns | Description |
|--------|---------|-------------|
| `start()` / `stop()` | — | Launch/disconnect (Chrome keeps running) |
| `is_logged_in()` | `bool` | Current login state |
| `wait_for_login(timeout)` | `bool` | Block until QR scan completes |
| `check_number(phone)` | `bool` | Is number on WhatsApp |
| `check_numbers(phones)` | `dict[str, bool]` | Batch verification |
| `open_chat(name_or_number)` | `bool` | Open a chat via search |
| `send_message(to, message)` | `bool` | Send a message (multiline supported) |
| `pin_chat(name_or_number)` | `dict` | Pin a chat (max 3 on WhatsApp Web) |
| `unpin_chat(name_or_number)` | `dict` | Unpin a chat |
| `create_group(name, members)` | `dict` | Create a group; returns `added` / `failed` member lists |
| `add_contact(phone, first_name, last_name="", sync_to_phone=False)` | `dict` | Add a new contact via the New Chat → New contact dialog |
| `read_last_messages(count=10)` | `list[dict]` | Structured messages: `{direction, sender, time, date, text}` |
| `read_last_messages_text(count=10)` | `list[str]` | Backcompat: just the text |
| `last_message(name_or_number)` | `dict \| None` | Open chat → last message, any direction |
| `last_incoming_message(name_or_number)` | `dict \| None` | Open chat → last `direction="in"` message |
| `list_chats(limit=50)` | `list[dict]` | Sidebar chats (scrolls virtualized grid) |
| `list_pinned_chats()` | `list[dict]` | Pinned chats (max 3) |
| `list_unread_chats(limit=50)` | `list[dict]` | Unread-only filter over `list_chats` |
| `unread_summary(limit=50)` | `dict` | `{chat_count, message_count, chats}` |
| `chat_list_total_count()` | `int` | Total chats WA reports in sidebar |

### Exceptions

| Exception | When |
|-----------|------|
| `LoginRequiredError` | QR code scan needed |
| `ChatNotFoundError` | Contact/number not found |
| `BrowserNotRunningError` | Chrome not reachable on CDP port |
| `BrowserLaunchError` | Failed to start Chrome |
| `NavigationError` | Failed to navigate to WA Web |
| `WhatsAppWebError` | Base class for all skill errors |

## Design Notes

- **Dedicated Chrome window** — Skill uses `--user-data-dir=/tmp/whatsapp-web/chrome_profile` + `--new-window` so it never hijacks your default Chrome profile.
- **Race-safe launch** — A `fcntl.flock` lockfile in the profile dir prevents two concurrent script runs from spawning duplicate Chrome processes.
- **Non-blocking by default** — `login.py` exits right after opening the window; agents stay responsive and don't appear frozen while a user scans the QR code.
- **Fast terminal-state exit** — Session readiness polls every 0.5s and returns as soon as login state is known (logged_in / qr_code), instead of waiting fixed sleeps.
- **DOM-first login detection** — Primary signals are DOM selectors (`#pane-side`, chat-list aria-labels); text matching is a fallback. Survives locale switches (English/Indonesian).
- **Virtualized chat list** — WA only renders visible rows, so `list_chats()` incrementally scrolls the sidebar grid and dedupes by display name.
- **Structured message parsing** — Reads WA's `data-pre-plain-text="[time, date] Sender: "` attribute and walks ancestors for `.message-in` / `.message-out` to detect direction. No CSS-selector chains, resilient to WA Web DOM churn.
- **DOM-driven waits** — Search, chat-open, and message-send use `wait_for_function` against DOM predicates (results rendered, chat header + composer present, composer cleared post-send) instead of fixed sleeps. Operations return as soon as WA is actually ready.
- **Anti-ban delay** — Configurable `between_delay` (default 0.75s) applied only between consecutive user-visible writes in a batch (e.g. `check_numbers` loop). Single-shot calls skip it entirely. Set to `0` for read-heavy scripts. Chrome is never killed by the skill.
- **Phone formatting** — Defaults to Indonesian numbers (+62); multiple format variants are tried during verification for accuracy.
