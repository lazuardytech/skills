"""Chat operations — open conversations, send and read messages."""

import asyncio
import logging

from .contacts import close_search, find_contact
from .errors import ChatNotFoundError

logger = logging.getLogger("src.chat")


async def open_chat(page, name_or_number: str, wait: float = 5.0) -> bool:
    """Open a chat with a contact by name or phone number.

    Searches for the contact via New Chat dialog, selects the first result.
    Returns True if chat was opened. Raises ChatNotFoundError if not found.
    """
    found = await find_contact(page, name_or_number, wait)
    if not found:
        await close_search(page)
        raise ChatNotFoundError(f"Contact not found: {name_or_number!r}")

    # Select the first search result
    await page.keyboard.press("Enter")
    await asyncio.sleep(1.5)
    logger.info("Opened chat with %r", name_or_number)
    return True


async def send_message(page, name_or_number: str, message: str, wait: float = 5.0) -> bool:
    """Send a message to a contact.

    Opens the chat (via search), types the message, and sends it.
    Returns True on success. Raises ChatNotFoundError if contact not found.
    """
    await open_chat(page, name_or_number, wait)

    # Type the message — handle multiline with Shift+Enter
    lines = message.split("\n")
    for i, line in enumerate(lines):
        if i > 0:
            await page.keyboard.press("Shift+Enter")
        await page.keyboard.type(line)

    # Send
    await page.keyboard.press("Enter")
    await asyncio.sleep(1.0)
    logger.info("Message sent to %r", name_or_number)
    return True


async def read_last_messages(page, count: int = 10) -> list[str]:
    """Read the last visible messages from the currently open chat.

    Returns a list of message strings (best-effort, text-based extraction).
    This reads the full page body and tries to extract recent message text.
    """
    body_text = await page.inner_text("body")
    lines = [line.strip() for line in body_text.split("\n") if line.strip()]
    # Return the last N non-empty lines as a rough approximation
    return lines[-count:] if len(lines) > count else lines
