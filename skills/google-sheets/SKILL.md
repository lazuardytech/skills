---
name: google-sheets
description: Google Sheets automation via the Sheets API. Use when the user needs to read data from a Google Sheet, read rows from a spreadsheet, get all records from a worksheet, update a cell in a Google Sheet, update a range of cells, batch update multiple cells, append a row to a spreadsheet, list worksheets in a spreadsheet, or perform any programmatic Google Sheets operation. Triggers include "read from Google Sheet", "baca Google Sheet", "update cell", "update sel", "append row", "tambah baris", "batch update", "list worksheets", "daftar worksheet", "get spreadsheet data", "ambil data spreadsheet", "write to sheet", "tulis ke sheet", or any task requiring Google Sheets read/write access.
license: Proprietary
compatibility: Requires Python 3.10+. Needs a service account credentials.json from Google Cloud Console.
metadata:
  author: lazuardy-tech
  version: "1.0"
---

## Setup Check

Before running any script, verify the skill is ready:
1. `credentials.json` exists in the working directory (or `--credentials <path>` is passed)
2. The target spreadsheet is shared with the service account `client_email`

If `credentials.json` is missing, tell the user:
> "This skill needs a Google service account key. Follow the setup guide in `skills/google-sheets/SETUP.md` to create one from Google Cloud Console."

If a script returns `403 PERMISSION_DENIED`, tell the user:
> "The service account doesn't have access to this spreadsheet. Share it with the `client_email` in your `credentials.json`."

If a script returns `SpreadsheetNotFound`, tell the user:
> "Spreadsheet not found or not shared. Make sure the URL is correct and the sheet is shared with the service account."

# google-sheets

Google Sheets read/write automation via the Sheets API and `gspread`.

## Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Enable **Google Sheets API** and **Google Drive API**
2. Create a Service Account → Keys → Add Key → JSON → download as `credentials.json`
3. Share the target spreadsheet with the service account email (found in `credentials.json` as `client_email`)
4. Place `credentials.json` in the working directory, or pass `--credentials <path>`

## Available Scripts

### Read all rows

```bash
python3 scripts/read_rows.py --url <spreadsheet_url>
python3 scripts/read_rows.py --url <spreadsheet_url> --worksheet 1
```

Output: `{"status": "ok", "worksheet": "Sheet1", "count": 42, "rows": [{"col": "val", ...}, ...]}`

### List worksheets

```bash
python3 scripts/list_worksheets.py --url <spreadsheet_url>
```

Output: `{"status": "ok", "spreadsheet": "My Sheet", "worksheets": [{"index": 0, "title": "Sheet1", "rows": 1000, "cols": 26}]}`

### Update a single cell

```bash
python3 scripts/update_cell.py --url <url> --row 2 --col 3 --value "Hello"
```

Output: `{"status": "updated", "worksheet": "Sheet1", "row": 2, "col": 3, "value": "Hello"}`

### Update a range

```bash
python3 scripts/update_range.py --url <url> --range A2:C3 --values "[[1,2,3],[4,5,6]]"
```

Output: `{"status": "updated", "worksheet": "Sheet1", "range": "A2:C3", "rows": 2}`

### Batch update multiple cells

```bash
python3 scripts/batch_update.py --url <url> --cell 2,1,Alice --cell 2,2,30
```

Output: `{"status": "updated", "worksheet": "Sheet1", "count": 2, "cells": [...]}`

### Append a row

```bash
python3 scripts/append_row.py --url <url> --values "Alice,30,Engineer"
```

Output: `{"status": "appended", "worksheet": "Sheet1", "values": ["Alice", "30", "Engineer"]}`

## Script Conventions

- Output: JSON to stdout, diagnostics to stderr
- Exit codes: `0` success · `1` error (credentials missing, API error, bad input)
- All scripts accept `--credentials <path>` to override the default `credentials.json` location
- `--worksheet` is always a zero-based index (default: `0`)
- `--values` for `update_range` expects a JSON 2D array string
- `--values` for `append_row` expects a comma-separated string

## Important Notes

- The service account must have edit access to the spreadsheet (share via the `client_email` in `credentials.json`)
- `credentials.json` is sensitive — never commit it to version control
- Scripts use PEP 723 inline dependencies — run with `uv run` or install `gspread` and `google-auth` manually
