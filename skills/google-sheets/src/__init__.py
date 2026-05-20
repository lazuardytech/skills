"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "gspread>=6.0",
#   "google-auth>=2.0",
# ]
# ///
Google Sheets client — shared by all scripts.
"""
from pathlib import Path
from google.oauth2.service_account import Credentials
import gspread

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_DEFAULT_CREDS = Path("credentials.json")


def get_client(credentials: str | None = None) -> gspread.Client:
    """Return an authenticated gspread client."""
    creds_path = Path(credentials) if credentials else _DEFAULT_CREDS
    if not creds_path.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {creds_path}. "
            "Download it from Google Cloud Console → APIs & Services → Credentials "
            "(Service Account → Keys → Add Key → JSON)."
        )
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return gspread.authorize(creds)


def open_sheet(url: str, credentials: str | None = None) -> gspread.Spreadsheet:
    return get_client(credentials).open_by_url(url)


def get_worksheet(url: str, index: int = 0, credentials: str | None = None) -> gspread.Worksheet:
    return open_sheet(url, credentials).get_worksheet(index)
