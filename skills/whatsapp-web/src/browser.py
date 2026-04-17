"""Chrome lifecycle management via CDP (Chrome DevTools Protocol)."""

import logging
import os
import platform
import subprocess
import time
import urllib.request

from .errors import BrowserLaunchError, BrowserNotRunningError

logger = logging.getLogger("src.browser")

DEFAULT_CDP_PORT = 9222
_CHROME_PATHS = {
    "Darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "Linux": "/usr/bin/google-chrome",
}


class ChromeBrowser:
    """Manages a Chrome instance with remote debugging enabled."""

    def __init__(
        self,
        user_data_dir: str | None = None,
        cdp_port: int = DEFAULT_CDP_PORT,
        chrome_path: str | None = None,
    ):
        if user_data_dir is None:
            user_data_dir = os.path.join(
                "/tmp", "whatsapp-web", "chrome_profile"
            )
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.cdp_port = cdp_port
        self.chrome_path = chrome_path or _CHROME_PATHS.get(platform.system())
        self._playwright = None
        self._browser = None

    def is_running(self) -> bool:
        """Check if Chrome is listening on the CDP port."""
        try:
            urllib.request.urlopen(
                f"http://localhost:{self.cdp_port}/json/version", timeout=2
            )
            return True
        except Exception:
            return False

    def ensure_running(self) -> bool:
        """Start Chrome if not already running. Returns True when ready."""
        if self.is_running():
            logger.info("Chrome already running on port %d", self.cdp_port)
            return True

        if not self.chrome_path or not os.path.exists(self.chrome_path):
            raise BrowserLaunchError(
                f"Chrome not found at {self.chrome_path!r}. "
                "Set chrome_path explicitly."
            )

        logger.info("Starting Chrome with CDP on port %d ...", self.cdp_port)
        # Detach Chrome from the parent process so it survives script exit.
        # This ensures subsequent script invocations reuse the same Chrome
        # window instead of spawning a new one.
        subprocess.Popen(
            [
                self.chrome_path,
                f"--user-data-dir={self.user_data_dir}",
                f"--remote-debugging-port={self.cdp_port}",
                "--disable-blink-features=AutomationControlled",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )

        for _ in range(15):
            if self.is_running():
                logger.info("Chrome ready")
                return True
            time.sleep(1)

        raise BrowserLaunchError(
            f"Chrome did not start within 15 seconds on port {self.cdp_port}"
        )

    async def connect(self, playwright):
        """Connect to Chrome via CDP. Returns (browser, context, page).

        Args:
            playwright: An async Playwright instance (from async_playwright().__aenter__()).
        """
        if not self.is_running():
            raise BrowserNotRunningError(
                f"Chrome is not running on port {self.cdp_port}. "
                "Call ensure_running() first."
            )

        browser = await playwright.chromium.connect_over_cdp(
            f"http://localhost:{self.cdp_port}"
        )
        context = browser.contexts[0]
        page = context.pages[0]
        self._browser = browser
        return browser, context, page

    async def disconnect(self):
        """Drop Playwright reference to Chrome (Chrome keeps running).

        Note: we do NOT call browser.close() — that would close Chrome itself.
        For CDP-attached browsers, just dropping the reference and closing
        the Playwright context is enough.
        """
        self._browser = None
