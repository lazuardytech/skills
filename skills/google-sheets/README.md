# google-sheets

Google Sheets read/write automation via the Sheets API and `gspread`.

## Setup

1. Enable **Google Sheets API** and **Google Drive API** in [Google Cloud Console](https://console.cloud.google.com/)
2. Create a Service Account → Keys → Add Key → JSON → save as `credentials.json`
3. Share the target spreadsheet with the service account's `client_email`
4. Place `credentials.json` in the working directory (or pass `--credentials <path>` to any script)

## Scripts

| Script | Description |
|--------|-------------|
| `read_rows.py` | Read all rows as list of dicts |
| `list_worksheets.py` | List all worksheets in a spreadsheet |
| `update_cell.py` | Update a single cell by row/col |
| `update_range.py` | Update a named range (A1 notation) |
| `batch_update.py` | Update multiple cells in one API call |
| `append_row.py` | Append a row to a worksheet |

## Usage

```bash
# Read all rows
python3 scripts/read_rows.py --url <spreadsheet_url>

# List worksheets
python3 scripts/list_worksheets.py --url <spreadsheet_url>

# Update a cell (row 2, col 3)
python3 scripts/update_cell.py --url <url> --row 2 --col 3 --value "Hello"

# Update a range
python3 scripts/update_range.py --url <url> --range A2:C3 --values "[[1,2,3],[4,5,6]]"

# Batch update
python3 scripts/batch_update.py --url <url> --cell 2,1,Alice --cell 2,2,30

# Append a row
python3 scripts/append_row.py --url <url> --values "Alice,30,Engineer"
```

All scripts output JSON to stdout. Pass `--worksheet <index>` to target a specific sheet (default: `0`).

## Notes

- `credentials.json` is sensitive — never commit it
- Scripts use [PEP 723](https://peps.python.org/pep-0723/) inline deps — run with `uv run` or install `gspread` + `google-auth` manually
- Python 3.10+ required
