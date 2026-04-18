"""Contact search and number verification on WhatsApp Web."""

import asyncio
import logging

from .phone import extract_digits, format_phone_wa_variants

logger = logging.getLogger("src.contacts")

DEFAULT_SEARCH_WAIT = 5.0


async def search_contact(page, query: str, wait: float = DEFAULT_SEARCH_WAIT) -> str:
    """Open New Chat dialog, type a query, and return page body text.

    The caller is responsible for calling close_search() afterwards.
    """
    await page.keyboard.press("Meta+Control+n")
    await asyncio.sleep(1.5)
    await page.keyboard.type(query)
    await asyncio.sleep(wait)
    return await page.inner_text("body")


async def close_search(page) -> None:
    """Dismiss the search dialog by pressing Escape."""
    await page.keyboard.press("Escape")
    await asyncio.sleep(0.5)


async def check_number(page, phone: str, wait: float = DEFAULT_SEARCH_WAIT) -> bool:
    """Check if a phone number is registered on WhatsApp.

    Returns True if the number is on WhatsApp, False otherwise.
    """
    try:
        body_text = await search_contact(page, phone, wait)
        body_lower = body_text.lower()

        # Pattern 1: explicit "no result"
        if "no result found" in body_lower or "no results found" in body_lower:
            return False

        # Pattern 2: formatted number visible in results (check all grouping variants)
        for formatted in format_phone_wa_variants(phone):
            if formatted in body_text:
                return True

        # Pattern 3: "not in your contacts" but number digits are visible
        if "not in your contacts" in body_lower:
            digits = extract_digits(phone)
            if len(digits) >= 6 and digits[-6:] in body_text:
                return True

        return False
    finally:
        await close_search(page)


async def find_contact(page, name_or_number: str, wait: float = DEFAULT_SEARCH_WAIT) -> bool:
    """Search for a contact by name or number.

    Returns True if found. Does NOT close the search dialog —
    use this when you want to select the result afterwards.
    """
    body_text = await search_contact(page, name_or_number, wait)
    body_lower = body_text.lower()

    if "no result found" in body_lower or "no results found" in body_lower:
        return False

    return True
