#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "gspread>=6.0",
#   "google-auth>=2.0",
# ]
# ///
"""Update a named range (e.g. A2:C5) in a worksheet."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src import get_worksheet


def main():
    parser = argparse.ArgumentParser(description="Update a range of cells in a Google Sheet.")
    parser.add_argument("--url", required=True, help="Spreadsheet URL")
    parser.add_argument("--range", required=True, dest="range_name", help="A1 notation range, e.g. A2:C5")
    parser.add_argument("--values", required=True, help="JSON 2D array, e.g. '[[1,2],[3,4]]'")
    parser.add_argument("--worksheet", type=int, default=0, help="Worksheet index (default: 0)")
    parser.add_argument("--credentials", default=None, help="Path to credentials.json")
    args = parser.parse_args()

    try:
        values = json.loads(args.values)
        ws = get_worksheet(args.url, args.worksheet, args.credentials)
        ws.update(args.range_name, values, value_input_option="USER_ENTERED")
        print(json.dumps({
            "status": "updated",
            "worksheet": ws.title,
            "range": args.range_name,
            "rows": len(values),
        }))
    except FileNotFoundError as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "error": f"Invalid --values JSON: {e}"}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
