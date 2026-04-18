"""Chat operations — open conversations, send and read messages, list chats."""

import asyncio
import logging

from .contacts import close_search, find_contact
from .errors import ChatNotFoundError

logger = logging.getLogger("src.chat")


# JS snippet that reads the currently-rendered chat rows from #pane-side.
# WA Web virtualizes the list, so only rows in viewport are in DOM.
_READ_VISIBLE_ROWS_JS = r"""
() => {
    const pane = document.querySelector('#pane-side');
    if (!pane) return {error: 'no pane-side'};
    const grid = pane.querySelector('[role="grid"]');
    if (!grid) return {error: 'no grid'};
    const totalCount = parseInt(grid.getAttribute('aria-rowcount') || '0', 10);
    const scrollContainer = pane.querySelector('[aria-label][style*="overflow"]')
        || grid.parentElement || pane;

    const rows = Array.from(grid.querySelectorAll('div[role="row"]'));
    const visible = rows.map(row => {
        const text = (row.innerText || '').trim();
        const icons = Array.from(row.querySelectorAll('[data-icon]'))
            .map(e => e.getAttribute('data-icon'));
        const svgTitles = Array.from(row.querySelectorAll('svg title'))
            .map(e => e.textContent);
        const top = row.getBoundingClientRect().top;
        const ariaLabels = Array.from(row.querySelectorAll('[aria-label]'))
            .map(e => e.getAttribute('aria-label')).filter(Boolean);
        return {text, icons, svgTitles, top, ariaLabels};
    });
    return {
        totalCount,
        rows: visible,
        scrollTop: scrollContainer.scrollTop,
        scrollHeight: scrollContainer.scrollHeight,
        clientHeight: scrollContainer.clientHeight,
    };
}
"""


def _row_is_pinned(row: dict) -> bool:
    icons = row.get("icons") or []
    titles = row.get("svgTitles") or []
    markers = set(icons) | set(titles)
    return any("push-pin" in m or "pinned" in m.lower() for m in markers)


def _row_display_name(row: dict) -> str:
    """Best-effort extract of the chat display name (first text line)."""
    text = row.get("text") or ""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return ""
    # First line is sometimes "N unread messages" — skip past those.
    for ln in lines:
        low = ln.lower()
        if "unread message" in low or "pesan belum dibaca" in low:
            continue
        return ln
    return lines[0]


async def _scroll_chat_list_to_top(page) -> None:
    await page.evaluate(
        """() => {
            const pane = document.querySelector('#pane-side');
            if (!pane) return;
            const grid = pane.querySelector('[role="grid"]');
            const scroller = grid?.parentElement || pane;
            scroller.scrollTop = 0;
        }"""
    )
    await asyncio.sleep(0.3)


async def list_chats(page, limit: int = 50) -> list[dict]:
    """Return up to `limit` chat entries from the top of the chat list.

    Each entry is a dict with keys: name, preview, pinned, raw.
    Scrolls the virtualized grid incrementally to surface more rows.
    """
    await _scroll_chat_list_to_top(page)

    seen_names: set[str] = set()
    ordered: list[dict] = []

    async def collect_once() -> dict:
        data = await page.evaluate(_READ_VISIBLE_ROWS_JS)
        if "error" in data:
            return data
        for row in data.get("rows", []):
            name = _row_display_name(row)
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            text = row.get("text", "")
            lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
            preview = lines[-1] if len(lines) >= 2 else ""
            ordered.append(
                {
                    "name": name,
                    "preview": preview,
                    "pinned": _row_is_pinned(row),
                    "raw": text,
                }
            )
            if len(ordered) >= limit:
                break
        return data

    # Initial collect.
    data = await collect_once()
    if "error" in data:
        return []

    # Scroll incrementally until we have enough rows or hit the bottom.
    max_scrolls = 25
    for _ in range(max_scrolls):
        if len(ordered) >= limit:
            break
        prev_count = len(ordered)
        # Page down by ~80% of viewport.
        done = await page.evaluate(
            """() => {
                const pane = document.querySelector('#pane-side');
                const grid = pane?.querySelector('[role="grid"]');
                const scroller = grid?.parentElement || pane;
                if (!scroller) return true;
                const before = scroller.scrollTop;
                scroller.scrollTop += scroller.clientHeight * 0.8;
                return scroller.scrollTop === before;  // true if couldn't scroll further
            }"""
        )
        await asyncio.sleep(0.4)
        data = await collect_once()
        if done and len(ordered) == prev_count:
            break

    return ordered[:limit]


async def list_pinned_chats(page) -> list[dict]:
    """Return the pinned chats (max 3 on WhatsApp Web).

    Pinned chats are always at the top of the list, so a single top-of-list
    read is enough without scrolling.
    """
    await _scroll_chat_list_to_top(page)
    data = await page.evaluate(_READ_VISIBLE_ROWS_JS)
    if "error" in data:
        return []
    result = []
    for row in data.get("rows", []):
        if not _row_is_pinned(row):
            # Pinned chats are contiguous at the top; first non-pinned = stop.
            if result:
                break
            continue
        name = _row_display_name(row)
        if not name:
            continue
        text = row.get("text", "")
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        preview = lines[-1] if len(lines) >= 2 else ""
        result.append(
            {
                "name": name,
                "preview": preview,
                "pinned": True,
                "raw": text,
            }
        )
        if len(result) >= 3:
            break
    return result


async def chat_list_total_count(page) -> int:
    """Return the total number of chats in the sidebar (all, not just visible)."""
    data = await page.evaluate(_READ_VISIBLE_ROWS_JS)
    if "error" in data:
        return 0
    return int(data.get("totalCount") or 0)


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
