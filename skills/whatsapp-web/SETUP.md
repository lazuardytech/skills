# Setup Guide — whatsapp-web

## Requirements

- Python 3.10+
- Google Chrome (installed, not Chromium)
- macOS or Linux

## First-Time Setup

Install Playwright and its Chrome driver:

```bash
pip install playwright
playwright install chrome
```

Or with `uv`:

```bash
uv run --with playwright playwright install chrome
```

## Login

Run once to open WhatsApp Web and scan the QR code:

```bash
python3 scripts/login.py
```

- Opens Chrome and navigates to web.whatsapp.com
- Scan the QR code from your phone (WhatsApp → Linked Devices → Link a Device)
- Chrome profile is saved to `/tmp/whatsapp-web/chrome_profile/` — no re-scan needed on subsequent runs

## Verify Setup

```bash
python3 scripts/login.py
# Expected: {"state": "logged_in"}
```

If you see `{"state": "qr_code", ...}`, scan the QR code and run again.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `{"state": "error", ...}` | Chrome not found or CDP failed — check Chrome is installed |
| `{"state": "qr_code", ...}` | Not logged in — scan QR code from your phone |
| `playwright._impl._errors.Error` | Run `playwright install chrome` |

## Notes

- Chrome is never killed between runs — it persists in the background
- Profile path: `/tmp/whatsapp-web/chrome_profile/`
- Phone numbers default to Indonesian format (+62)
