#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "gspread>=6.0",
#   "google-auth>=2.0",
# ]
# ///
"""Batch-update multiple cells in one API call."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src import get_worksheet


def main():
    parser = argparse.ArgumentParser(
        description="Batch-update cells in a Google Sheet.",
        epilog="Each --cell must be in row,col,value format. Example: --cell 2,3,Hello",
    )
    parser.add_argument("--url", required=True, help="Spreadsheet URL")
    parser.add_argument(
        "--cell",
        dest="cells",
        action="append",
        required=True,
        metavar="ROW,COL,VALUE",
        help="Cell to update (repeatable)",
    )
    parser.add_argument("--worksheet", type=int, default=0, help="Worksheet index (default: 0)")
    parser.add_argument("--credentials", default=None, help="Path to credentials.json")
    args = parser.parse_args()

    try:
        ws = get_worksheet(args.url, args.worksheet, args.credentials)
        cell_list = []
        parsed = []
        for entry in args.cells:
            parts = entry.split(",", 2)
            if len(parts) != 3:
                raise ValueError(f"Invalid --cell format: {entry!r}. Expected row,col,value")
            row, col, value = int(parts[0]), int(parts[1]), parts[2]
            c = ws.cell(row, col)
            c.value = value
            cell_list.append(c)
            parsed.append({"row": row, "col": col, "value": value})

        ws.update_cells(cell_list, value_input_option="USER_ENTERED")
        print(json.dumps({"status": "updated", "worksheet": ws.title, "count": len(cell_list), "cells": parsed}))
    except FileNotFoundError as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
