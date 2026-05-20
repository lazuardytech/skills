# Setup Guide — google-sheets

## Requirements

- Python 3.10+
- A Google Cloud project with **Google Sheets API** and **Google Drive API** enabled
- A service account with a JSON key (`credentials.json`)
- The target spreadsheet shared with the service account

## Step-by-Step

### 1. Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project
3. Navigate to **APIs & Services → Library**
4. Search and enable:
   - **Google Sheets API**
   - **Google Drive API**

### 2. Create a Service Account

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → Service Account**
3. Give it a name (e.g. `sheets-agent`) and click **Done**

### 3. Download the JSON Key

1. Click the service account you just created
2. Go to **Keys → Add Key → Create new key → JSON**
3. Save the downloaded file as `credentials.json`
4. Place it in your working directory (or pass `--credentials <path>` to any script)

> **Never commit `credentials.json` to version control.**

### 4. Share the Spreadsheet

1. Open `credentials.json` and copy the `client_email` value
2. Open your Google Sheet
3. Click **Share** and add the `client_email` with **Editor** access

## Verify Setup

```bash
python3 scripts/list_worksheets.py --url <your_spreadsheet_url>
# Expected: {"status": "ok", "spreadsheet": "...", "worksheets": [...]}
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `credentials.json not found` | File missing or wrong path — pass `--credentials <path>` |
| `403 PERMISSION_DENIED` | Sheets API or Drive API not enabled in Cloud Console |
| `gspread.exceptions.SpreadsheetNotFound` | Spreadsheet not shared with the service account `client_email` |
| `google.auth.exceptions.DefaultCredentialsError` | Invalid or corrupted `credentials.json` |

## Notes

- One `credentials.json` works for all spreadsheets — just share each sheet with the same `client_email`
- Scripts use [PEP 723](https://peps.python.org/pep-0723/) inline deps — run with `uv run` or install manually:
  ```bash
  pip install gspread google-auth
  ```
