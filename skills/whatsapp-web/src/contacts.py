"""Contact search and number verification on WhatsApp Web."""

import asyncio
import logging

from .phone import extract_digits, format_phone_wa_variants

logger = logging.getLogger("src.contacts")

DEFAULT_SEARCH_WAIT = 2.5

# JS: true once the search dialog has finished reacting to the query —
# either results rendered, or an explicit "no result" message is shown.
# Using document-level text because WA Web's result list selector shifts.
_SEARCH_READY_JS = r"""
() => {
    const body = document.body?.innerText || '';
    const low = body.toLowerCase();
    if (low.includes('no result found') || low.includes('no results found')
        || low.includes('tidak ada hasil')) return true;
    // Result rows appear inside a listbox/grid inside the dialog.
    const items = document.querySelectorAll(
        '[role="listbox"] [role="option"], [role="listbox"] [role="listitem"], '
        + 'div[role="dialog"] [role="row"]'
    );
    return items.length > 0;
}
"""


async def _wait_for(page, js: str, timeout_s: float, poll_s: float = 0.1) -> bool:
    """Poll a JS predicate until truthy or timeout. Returns whether it became truthy."""
    try:
        await page.wait_for_function(js, timeout=int(timeout_s * 1000), polling=int(poll_s * 1000))
        return True
    except Exception:
        return False


async def search_contact(page, query: str, wait: float = DEFAULT_SEARCH_WAIT) -> str:
    """Open New Chat dialog, type a query, and return page body text.

    The caller is responsible for calling close_search() afterwards.
    """
    await page.keyboard.press("Meta+Control+n")
    # Dialog render is fast; short floor + DOM check keeps us correct.
    await asyncio.sleep(0.25)
    await page.keyboard.type(query)
    # Wait for results (or explicit no-result message) instead of fixed sleep.
    await _wait_for(page, _SEARCH_READY_JS, timeout_s=wait)
    return await page.inner_text("body")


async def close_search(page) -> None:
    """Dismiss the search dialog by pressing Escape."""
    await page.keyboard.press("Escape")
    await asyncio.sleep(0.1)


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
