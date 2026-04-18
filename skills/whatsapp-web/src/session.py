"""WhatsApp Web session management — login detection and navigation."""

import asyncio
import logging

from .errors import LoginRequiredError, NavigationError

logger = logging.getLogger("src.session")

# DOM selectors checked first — resilient to WA Web copy changes and locale.
_LOGGED_IN_SELECTORS = [
    "#pane-side",  # Left chat-list pane
    'div[aria-label="Chat list"]',
    'div[aria-label="Daftar chat"]',  # id
    'header[data-testid="chatlist-header"]',
    'div[data-testid="chat-list"]',
    '[data-testid="menu-bar-menu"]',
]
_QR_SELECTORS = [
    'canvas[aria-label*="Scan"]',
    'canvas[aria-label*="scan"]',
    "div[data-ref]",  # QR container has data-ref attr
    'canvas[role="img"]',
]

# Text fallbacks — multi-language. Used only when DOM check is inconclusive.
_QR_PATTERNS = [
    "link a device",
    "use whatsapp on your computer",
    "phone to scan",
    "scan this qr",
    "scan the qr",
    "log in with phone number",
    # Indonesian
    "tautkan perangkat",
    "gunakan whatsapp di komputer",
    "pindai kode qr",
    "masuk dengan nomor telepon",
]
_LOGGED_IN_PATTERNS = [
    "search or start new chat",
    "search or start a new chat",
    # Indonesian
    "cari atau mulai chat baru",
    "cari atau mulai obrolan baru",
    # Generic
    "archived",
    "diarsipkan",
]
_LOADING_PATTERNS = [
    "connecting",
    "menghubungkan",
    "loading your chats",
    "memuat obrolan",
]


class WhatsAppSession:
    """Handles navigation to WhatsApp Web and login state detection."""

    def __init__(self, page):
        self.page = page

    async def navigate(self, settle_timeout: float = 6.0) -> None:
        """Ensure the page is on WhatsApp Web, settling only as long as needed.

        - Not on WA Web → goto, then poll until logged_in/qr_code (fast exit).
        - Already on WA Web and logged in → no-op.
        - Already on WA Web but not yet ready → reload + poll.

        The settle loop polls every 0.5s and returns as soon as we detect a
        terminal state. Upper bound = settle_timeout (default 6s). That way
        a logged-in session exits in ~0.5s, while a first-load QR state also
        exits as soon as the QR renders.
        """
        try:
            if "web.whatsapp.com" not in self.page.url:
                logger.info("Opening WhatsApp Web...")
                await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
                await self._settle(settle_timeout)
                return

            state = await self.get_login_state()
            if state == "logged_in":
                logger.info("WhatsApp Web is already open and ready")
                return
            logger.info("Refreshing WhatsApp Web...")
            await self.page.reload(wait_until="domcontentloaded")
            await self._settle(settle_timeout)
        except Exception as e:
            raise NavigationError(f"Couldn't open WhatsApp Web: {e}") from e

    async def _settle(self, timeout: float) -> str:
        """Poll login state until it stabilises or timeout.

        Returns the last observed state. A logged-in or qr_code state is
        considered terminal and returns immediately.
        """
        interval = 0.25
        elapsed = 0.0
        state = "unknown"
        while elapsed < timeout:
            state = await self.get_login_state()
            if state in ("logged_in", "qr_code"):
                return state
            await asyncio.sleep(interval)
            elapsed += interval
        return state

    async def get_login_state(self) -> str:
        """Detect current login state.

        Returns one of: "logged_in", "qr_code", "loading", "unknown".

        Strategy: DOM selectors first (language-agnostic and resilient to
        UI copy changes), text-body fallback second.
        """
        # --- DOM-first detection ---
        if await self._any_selector_matches(_LOGGED_IN_SELECTORS):
            return "logged_in"
        if await self._any_selector_matches(_QR_SELECTORS):
            # QR surface can also appear briefly while logged-in page still
            # booting — ensure no chat-list is present before calling it qr_code.
            if not await self._any_selector_matches(_LOGGED_IN_SELECTORS):
                return "qr_code"

        # --- Text fallback ---
        try:
            body_text = (await self.page.inner_text("body")).lower()
        except Exception:
            return "unknown"

        for pattern in _LOGGED_IN_PATTERNS:
            if pattern in body_text:
                return "logged_in"
        for pattern in _QR_PATTERNS:
            if pattern in body_text:
                return "qr_code"
        for pattern in _LOADING_PATTERNS:
            if pattern in body_text:
                return "loading"

        return "unknown"

    async def _any_selector_matches(self, selectors: list[str]) -> bool:
        """Return True if any of the given CSS selectors is attached to DOM."""
        for sel in selectors:
            try:
                loc = self.page.locator(sel).first
                if await loc.count() > 0:
                    return True
            except Exception:
                continue
        return False

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
            state = await self._settle(timeout=10.0)

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
