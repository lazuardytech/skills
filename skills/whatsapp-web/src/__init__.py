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
from .chat import chat_list_total_count as _chat_list_total_count
from .chat import last_incoming_message as _last_incoming_message
from .chat import last_message as _last_message
from .chat import list_chats as _list_chats
from .chat import list_pinned_chats as _list_pinned_chats
from .chat import list_unread_chats as _list_unread_chats
from .chat import open_chat as _open_chat
from .chat import pin_chat as _pin_chat
from .chat import read_last_messages as _read_last_messages
from .chat import read_last_messages_text as _read_last_messages_text
from .chat import send_message as _send_message
from .chat import unpin_chat as _unpin_chat
from .chat import unread_summary as _unread_summary
from .contacts import add_contact as _add_contact
from .contacts import check_number as _check_number
from .errors import (
    BrowserLaunchError,
    BrowserNotRunningError,
    ChatNotFoundError,
    LoginRequiredError,
    NavigationError,
    WhatsAppWebError,
)
from .groups import create_group as _create_group
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
        between_delay: Seconds to wait between consecutive user-visible
            operations (anti-ban). Only applied between calls that type,
            send, or open chats — not read-only operations. Set to 0 for
            no inter-op delay (e.g. read-heavy scripts).
    """

    def __init__(
        self,
        chrome_profile_dir: str | None = None,
        cdp_port: int = 9222,
        chrome_path: str | None = None,
        between_delay: float = 0.75,
    ):
        self._chrome = ChromeBrowser(
            user_data_dir=chrome_profile_dir,
            cdp_port=cdp_port,
            chrome_path=chrome_path,
        )
        self._between_delay = between_delay
        self._pw_cm = None
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
        self._pw_cm = async_playwright()
        self._playwright = await self._pw_cm.__aenter__()
        self._browser, self._context, self._page = await self._chrome.connect(self._playwright)
        self._session = WhatsAppSession(self._page)
        await self._session.ensure_ready()

    async def stop(self) -> None:
        """Disconnect from Chrome (Chrome keeps running)."""
        if self._pw_cm is not None:
            await self._pw_cm.__aexit__(None, None, None)
            self._pw_cm = None
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
        return await _check_number(self._page, phone)

    async def check_numbers(self, phones: list[str]) -> dict[str, bool]:
        """Batch-check multiple phone numbers.

        Returns a dict mapping phone -> True/False.
        """
        results: dict[str, bool] = {}
        for i, phone in enumerate(phones):
            if i > 0 and self._between_delay > 0:
                await asyncio.sleep(self._between_delay)
            results[phone] = await self.check_number(phone)
        return results

    async def add_contact(
        self,
        phone: str,
        first_name: str,
        last_name: str = "",
        sync_to_phone: bool = False,
    ) -> dict:
        """Add a new contact via the New Chat → New contact dialog.

        Returns {status, first_name, last_name, phone, sync_to_phone}.
        """
        return await _add_contact(
            self._page,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            sync_to_phone=sync_to_phone,
        )

    # --- Chat operations ---

    async def open_chat(self, name_or_number: str) -> bool:
        """Open a chat with a contact by name or phone number."""
        return await _open_chat(self._page, name_or_number)

    async def send_message(self, to: str, message: str) -> bool:
        """Send a message to a contact."""
        return await _send_message(self._page, to, message)

    async def pin_chat(self, name_or_number: str) -> dict:
        """Pin a chat in the sidebar (max 3 pins on WhatsApp Web)."""
        return await _pin_chat(self._page, name_or_number)

    async def unpin_chat(self, name_or_number: str) -> dict:
        """Unpin a chat in the sidebar."""
        return await _unpin_chat(self._page, name_or_number)

    async def create_group(self, name: str, members: list[str]) -> dict:
        """Create a new WhatsApp group with the given name and members.

        Members can be contact names or phone numbers. Returns
        {status, name, requested_members, added, failed}.
        """
        return await _create_group(self._page, name=name, members=members)

    async def read_last_messages(self, count: int = 10) -> list[dict]:
        """Read the last visible messages from the currently open chat.

        Returns a list of dicts: {direction, sender, time, date, text}.
        """
        return await _read_last_messages(self._page, count)

    async def read_last_messages_text(self, count: int = 10) -> list[str]:
        """Backward-compatible: return just message texts."""
        return await _read_last_messages_text(self._page, count)

    async def last_message(self, name_or_number: str) -> dict | None:
        """Open a chat and return the very last message (any direction)."""
        return await _last_message(self._page, name_or_number)

    async def last_incoming_message(self, name_or_number: str) -> dict | None:
        """Open a chat and return the last *received* message from the contact."""
        return await _last_incoming_message(self._page, name_or_number)

    # --- Chat list ---

    async def list_chats(self, limit: int = 50) -> list[dict]:
        """List up to `limit` chats from the top of the sidebar."""
        return await _list_chats(self._page, limit)

    async def list_pinned_chats(self) -> list[dict]:
        """List pinned chats (max 3 on WhatsApp Web)."""
        return await _list_pinned_chats(self._page)

    async def chat_list_total_count(self) -> int:
        """Return the total number of chats in the sidebar."""
        return await _chat_list_total_count(self._page)

    async def list_unread_chats(self, limit: int = 50) -> list[dict]:
        """List chats with unread messages (within the top `limit` rows)."""
        return await _list_unread_chats(self._page, limit)

    async def unread_summary(self, limit: int = 50) -> dict:
        """Return unread chat count, total unread messages, and the chats."""
        return await _unread_summary(self._page, limit)

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
