"""WhatsApp Web automation skill for Lazuardy Tech.

Usage:
    from src import WhatsAppWeb

    async with WhatsAppWeb() as wa:
        await wa.check_number("081234567890")
        await wa.send_message("Ezra", "Hello!")
"""

import asyncio
import logging

from playwright.async_api import async_playwright

from .browser import ChromeBrowser
from .chat import open_chat as _open_chat
from .chat import read_last_messages as _read_last_messages
from .chat import send_message as _send_message
from .contacts import check_number as _check_number
from .errors import (
    BrowserLaunchError,
    BrowserNotRunningError,
    ChatNotFoundError,
    LoginRequiredError,
    NavigationError,
    WhatsAppWebError,
)
from .phone import format_phone_wa, format_phone_wa_variants
from .session import WhatsAppSession

logger = logging.getLogger("src")

__all__ = [
    "WhatsAppWeb",
    "WhatsAppWebError",
    "BrowserNotRunningError",
    "BrowserLaunchError",
    "LoginRequiredError",
    "NavigationError",
    "ChatNotFoundError",
    "format_phone_wa",
    "format_phone_wa_variants",
]


class WhatsAppWeb:
    """High-level interface for WhatsApp Web automation.

    Args:
        chrome_profile_dir: Path to Chrome user data directory.
        cdp_port: Chrome DevTools Protocol port (default 9222).
        chrome_path: Path to Chrome executable (auto-detected if None).
        between_delay: Seconds to wait between consecutive operations (anti-ban).
    """

    def __init__(
        self,
        chrome_profile_dir: str | None = None,
        cdp_port: int = 9222,
        chrome_path: str | None = None,
        between_delay: float = 3.0,
    ):
        self._chrome = ChromeBrowser(
            user_data_dir=chrome_profile_dir,
            cdp_port=cdp_port,
            chrome_path=chrome_path,
        )
        self._between_delay = between_delay
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._session = None

    async def start(self) -> None:
        """Start Chrome, connect via CDP, navigate to WhatsApp Web.

        Raises LoginRequiredError if QR code scan is needed.
        """
        self._chrome.ensure_running()
        self._playwright = await async_playwright().__aenter__()
        self._browser, self._context, self._page = await self._chrome.connect(
            self._playwright
        )
        self._session = WhatsAppSession(self._page)
        await self._session.ensure_ready()

    async def stop(self) -> None:
        """Disconnect from Chrome (Chrome keeps running)."""
        if self._playwright:
            await self._playwright.__aexit__(None, None, None)
            self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._session = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()

    @property
    def page(self):
        """Direct access to the Playwright Page for advanced usage."""
        return self._page

    @property
    def session(self) -> WhatsAppSession:
        """Access the session manager (login state, navigation)."""
        return self._session

    # --- Number verification ---

    async def check_number(self, phone: str) -> bool:
        """Check if a phone number is registered on WhatsApp."""
        result = await _check_number(self._page, phone)
        await asyncio.sleep(self._between_delay)
        return result

    async def check_numbers(self, phones: list[str]) -> dict[str, bool]:
        """Batch-check multiple phone numbers.

        Returns a dict mapping phone -> True/False.
        """
        results = {}
        for phone in phones:
            results[phone] = await self.check_number(phone)
        return results

    # --- Chat operations ---

    async def open_chat(self, name_or_number: str) -> bool:
        """Open a chat with a contact by name or phone number."""
        result = await _open_chat(self._page, name_or_number)
        await asyncio.sleep(self._between_delay)
        return result

    async def send_message(self, to: str, message: str) -> bool:
        """Send a message to a contact."""
        result = await _send_message(self._page, to, message)
        await asyncio.sleep(self._between_delay)
        return result

    async def read_last_messages(self, count: int = 10) -> list[str]:
        """Read the last visible messages from the currently open chat."""
        return await _read_last_messages(self._page, count)

    # --- Session state ---

    async def is_logged_in(self) -> bool:
        """Check if WhatsApp Web is currently logged in."""
        state = await self._session.get_login_state()
        return state == "logged_in"

    async def wait_for_login(self, timeout: int = 120) -> bool:
        """Wait for QR code scan to complete.

        Returns True when logged in. Raises LoginRequiredError on timeout.
        """
        return await self._session.wait_for_login(timeout)
