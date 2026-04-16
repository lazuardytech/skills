"""Custom exceptions for WhatsApp Web automation."""


class WhatsAppWebError(Exception):
    """Base exception for all WhatsApp Web errors."""


class BrowserNotRunningError(WhatsAppWebError):
    """Chrome is not reachable on the CDP port."""


class BrowserLaunchError(WhatsAppWebError):
    """Failed to start Chrome."""


class LoginRequiredError(WhatsAppWebError):
    """WhatsApp Web is showing QR code — user must scan from phone."""


class NavigationError(WhatsAppWebError):
    """Failed to navigate to WhatsApp Web."""


class ChatNotFoundError(WhatsAppWebError):
    """Contact or number search yielded no results."""
