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
        """Navigate to WhatsApp Web (or reload if already there)."""
        try:
            if "web.whatsapp.com" not in self.page.url:
                logger.info("Navigating to WhatsApp Web...")
                await self.page.goto(
                    "https://web.whatsapp.com", wait_until="domcontentloaded"
                )
                await asyncio.sleep(5)
            else:
                logger.info("Already on WhatsApp Web, reloading...")
                await self.page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(3)
        except Exception as e:
            raise NavigationError(f"Failed to navigate to WhatsApp Web: {e}") from e

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
                logger.info("WhatsApp Web is logged in")
                return True
            if state == "qr_code":
                logger.info("QR code detected — waiting for scan... (%ds/%ds)", elapsed, timeout)
            await asyncio.sleep(interval)
            elapsed += interval

        raise LoginRequiredError(
            f"WhatsApp Web login timed out after {timeout}s. "
            "Please scan the QR code from your phone."
        )

    async def ensure_ready(self) -> None:
        """Navigate to WA Web and verify we're logged in.

        Raises LoginRequiredError if QR code is shown.
        """
        await self.navigate()
        state = await self.get_login_state()

        if state == "loading":
            logger.info("WhatsApp Web is loading, waiting...")
            await asyncio.sleep(10)
            state = await self.get_login_state()

        if state == "qr_code":
            raise LoginRequiredError(
                "WhatsApp Web requires QR code login. "
                "Please scan the QR code from your phone, then call wait_for_login()."
            )

        if state == "logged_in":
            logger.info("WhatsApp Web session is ready")
            return

        # "unknown" — might be logged in with different locale, proceed optimistically
        logger.warning("Could not confirm login state (got %r), proceeding anyway", state)
