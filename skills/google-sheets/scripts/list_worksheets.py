#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "gspread>=6.0",
#   "google-auth>=2.0",
# ]
# ///
"""List all worksheets in a spreadsheet."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src import open_sheet


def main():
    parser = argparse.ArgumentParser(description="List worksheets in a Google Spreadsheet.")
    parser.add_argument("--url", required=True, help="Spreadsheet URL")
    parser.add_argument("--credentials", default=None, help="Path to credentials.json")
    args = parser.parse_args()

    try:
        spreadsheet = open_sheet(args.url, args.credentials)
        sheets = [
            {"index": i, "title": ws.title, "rows": ws.row_count, "cols": ws.col_count}
            for i, ws in enumerate(spreadsheet.worksheets())
        ]
        print(json.dumps({"status": "ok", "spreadsheet": spreadsheet.title, "worksheets": sheets}))
    except FileNotFoundError as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
