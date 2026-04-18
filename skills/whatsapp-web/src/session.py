"""WhatsApp Web session management — login detection and navigation."""

import asyncio
import logging

from .errors import LoginRequiredError, NavigationError

logger = logging.getLogger("src.session")

# Text patterns used to detect WhatsApp Web login state (case-insensitive)
_QR_PATTERNS = [
    "link a device",
    "use whatsapp on your computer",
    "phone to scan",
    "scan this qr",
    "log in with phone number",
]
_LOGGED_IN_PATTERNS = [
    "search or start new chat",
    "search or start a new chat",
]
_LOADING_PATTERNS = [
    "connecting",
]


class WhatsAppSession:
    """Handles navigation to WhatsApp Web and login state detection."""

    def __init__(self, page):
        self.page = page

    async def navigate(self) -> None:
        """Ensure the page is on WhatsApp Web.

        - Not on WA Web → goto.
        - Already on WA Web and logged in → no-op (don't spam reloads).
        - Already on WA Web but not yet ready → reload.
        """
        try:
            if "web.whatsapp.com" not in self.page.url:
                logger.info("Opening WhatsApp Web...")
                await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
                await asyncio.sleep(5)
                return

            state = await self.get_login_state()
            if state == "logged_in":
                logger.info("WhatsApp Web is already open and ready")
                return
            logger.info("Refreshing WhatsApp Web...")
            await self.page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(3)
        except Exception as e:
            raise NavigationError(f"Couldn't open WhatsApp Web: {e}") from e

    async def get_login_state(self) -> str:
        """Detect current login state.

        Returns one of: "logged_in", "qr_code", "loading", "unknown"
        """
        try:
            body_text = (await self.page.inner_text("body")).lower()
        except Exception:
            return "unknown"

        for pattern in _QR_PATTERNS:
            if pattern in body_text:
                return "qr_code"

        for pattern in _LOGGED_IN_PATTERNS:
            if pattern in body_text:
                return "logged_in"

        for pattern in _LOADING_PATTERNS:
            if pattern in body_text:
                return "loading"

        return "unknown"

    async def wait_for_login(self, timeout: int = 120) -> bool:
        """Poll until logged in or timeout.

        Returns True when logged in. Raises LoginRequiredError on timeout.
        """
        elapsed = 0
        interval = 3
        while elapsed < timeout:
            state = await self.get_login_state()
            if state == "logged_in":
                logger.info("WhatsApp Web is ready")
                return True
            if state == "qr_code":
                logger.info(
                    "Please scan the QR code with your phone... (%ds/%ds)",
                    elapsed,
                    timeout,
                )
            await asyncio.sleep(interval)
            elapsed += interval

        raise LoginRequiredError(
            f"We didn't detect a successful login within {timeout}s. "
            "Please scan the QR code with your phone and try again."
        )

    async def ensure_ready(self) -> None:
        """Navigate to WA Web and verify we're logged in.

        Raises LoginRequiredError if QR code is shown.
        """
        await self.navigate()
        state = await self.get_login_state()

        if state == "loading":
            logger.info("Getting WhatsApp Web ready...")
            await asyncio.sleep(10)
            state = await self.get_login_state()

        if state == "qr_code":
            raise LoginRequiredError(
                "WhatsApp Web needs you to sign in. "
                "Please scan the QR code with your phone, then try again."
            )

        if state == "logged_in":
            logger.info("WhatsApp Web is ready")
            return

        # "unknown" — might be logged in with different locale, proceed optimistically
        logger.warning("Couldn't fully confirm WhatsApp Web is ready, continuing anyway")
