"""Chat operations — open conversations, send and read messages, list chats."""

import asyncio
import logging
import re

from .contacts import _wait_for, close_search, find_contact
from .errors import ChatNotFoundError

# JS: true once the main chat pane shows a conversation header (contact name
# and the message composer area). We don't rely on a specific selector chain
# because WA rewrites them often — header + footer composer presence is enough.
_CHAT_OPEN_JS = r"""
() => {
    const main = document.querySelector('#main');
    if (!main) return false;
    const header = main.querySelector('header');
    const footer = main.querySelector('footer');
    // Composer is a contenteditable div inside the footer.
    const composer = footer?.querySelector('div[contenteditable="true"]');
    return !!(header && composer);
}
"""

# JS: the composer is empty again after a send. Combined with a small floor
# this is more reliable than waiting on a send-tick icon, which varies.
_COMPOSER_EMPTY_JS = r"""
() => {
    const main = document.querySelector('#main');
    const composer = main?.querySelector('footer div[contenteditable="true"]');
    if (!composer) return false;
    return (composer.innerText || '').trim() === '';
}
"""

logger = logging.getLogger("src.chat")

# Matches aria-labels like "3 unread messages", "1 unread message",
# "3 pesan belum dibaca", "unread" (muted chats marked unread w/o count).
_UNREAD_ARIA_RE = re.compile(
    r"(\d+)\s+(?:unread|pesan\s+belum\s+dibaca)|unread\b|belum\s+dibaca",
    re.IGNORECASE,
)
_UNREAD_COUNT_RE = re.compile(r"(\d+)\s+(?:unread|pesan\s+belum\s+dibaca)", re.IGNORECASE)


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


def _row_unread(row: dict) -> tuple[bool, int]:
    """Return (is_unread, unread_count).

    - Numeric count comes from the aria-label "N unread messages" or from
      the row text. Missing count (e.g. "unread" on a muted chat marked
      unread manually) is treated as unread with count 0.
    """
    aria_labels = row.get("ariaLabels") or []
    text = row.get("text") or ""

    for label in aria_labels:
        m = _UNREAD_COUNT_RE.search(label)
        if m:
            return True, int(m.group(1))
        if _UNREAD_ARIA_RE.search(label):
            return True, 0

    # Fallback to row text — first line is often "N unread messages".
    m = _UNREAD_COUNT_RE.search(text)
    if m:
        return True, int(m.group(1))
    if _UNREAD_ARIA_RE.search(text):
        return True, 0

    return False, 0


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
    await asyncio.sleep(0.1)


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
            is_unread, unread_count = _row_unread(row)
            ordered.append(
                {
                    "name": name,
                    "preview": preview,
                    "pinned": _row_is_pinned(row),
                    "unread": is_unread,
                    "unread_count": unread_count,
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
        await asyncio.sleep(0.2)
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
        is_unread, unread_count = _row_unread(row)
        result.append(
            {
                "name": name,
                "preview": preview,
                "pinned": True,
                "unread": is_unread,
                "unread_count": unread_count,
                "raw": text,
            }
        )
        if len(result) >= 3:
            break
    return result


async def list_unread_chats(page, limit: int = 50) -> list[dict]:
    """Return chats with unread messages, scanning the top `limit` rows.

    Uses list_chats() internally and filters. Pass a larger limit to cover
    deeper parts of the sidebar if you have many chats.
    """
    chats = await list_chats(page, limit=limit)
    return [c for c in chats if c.get("unread")]


async def unread_summary(page, limit: int = 50) -> dict:
    """Return {'chat_count', 'message_count', 'chats'} for unread chats."""
    unread = await list_unread_chats(page, limit=limit)
    total_msgs = sum(c.get("unread_count") or 0 for c in unread)
    return {
        "chat_count": len(unread),
        "message_count": total_msgs,
        "chats": unread,
    }


async def chat_list_total_count(page) -> int:
    """Return the total number of chats in the sidebar (all, not just visible)."""
    data = await page.evaluate(_READ_VISIBLE_ROWS_JS)
    if "error" in data:
        return 0
    return int(data.get("totalCount") or 0)


async def open_chat(page, name_or_number: str, wait: float = 2.5) -> bool:
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
    # Wait for the chat pane to actually open instead of a fixed sleep.
    await _wait_for(page, _CHAT_OPEN_JS, timeout_s=wait)
    logger.info("Opened chat with %r", name_or_number)
    return True


# JS: open the chat header menu (three-dots "Menu" button). Returns true
# once the menu popup is attached to the DOM.
_OPEN_HEADER_MENU_JS = r"""
() => {
    const main = document.querySelector('#main');
    const header = main?.querySelector('header');
    if (!header) return false;
    const buttons = [...header.querySelectorAll('[role="button"], button, div[aria-label]')];
    const want = /^(menu|lainnya|more)$/i;
    for (const el of buttons) {
        const label = (el.getAttribute('aria-label') || el.getAttribute('title') || '').trim();
        if (want.test(label)) { el.click(); return true; }
    }
    // Fallback: last button in the header is usually the menu trigger.
    const last = buttons[buttons.length - 1];
    if (last) { last.click(); return true; }
    return false;
}
"""

# JS: the header popup menu is open once a listbox/menu with multiple items
# exists in the DOM. WA uses role="application" + div[role="button"] inside.
_HEADER_MENU_OPEN_JS = r"""
() => {
    const lists = document.querySelectorAll(
        'div[role="application"] [role="menu"], ul[role="menu"], '
        + 'div[aria-label*="menu" i], div[role="listbox"]'
    );
    for (const l of lists) {
        const items = l.querySelectorAll('[role="menuitem"], li, div[role="button"]');
        if (items.length >= 2) return true;
    }
    return false;
}
"""

# JS: click an item in an open popup menu by matching its label. Accepts a
# list of regex strings (JS flavored) to try in order. Returns true on click.
_CLICK_MENU_ITEM_JS = r"""
(patterns) => {
    const regs = patterns.map(p => new RegExp(p, 'i'));
    const candidates = [...document.querySelectorAll(
        '[role="menuitem"], [role="menu"] li, [role="menu"] div[role="button"], '
        + 'div[role="application"] div[role="button"], ul[role="menu"] li'
    )];
    for (const el of candidates) {
        const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
        for (const re of regs) {
            if (re.test(label)) { el.click(); return label; }
        }
    }
    return null;
}
"""


async def _close_any_popup(page) -> None:
    """Best-effort close for stray menus/dialogs via Escape."""
    try:
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.1)
    except Exception:
        pass


async def _is_pinned_in_sidebar(page, name: str) -> bool | None:
    """Return True/False if a sidebar row for `name` exists, else None.

    Uses the same row-reader the list_chats() function uses, so a chat that
    isn't in the top-of-list view may return None — the caller should treat
    None as "unknown" rather than "not pinned".
    """
    data = await page.evaluate(_READ_VISIBLE_ROWS_JS)
    if "error" in data:
        return None
    for row in data.get("rows", []):
        if _row_display_name(row).strip().lower() == name.strip().lower():
            return _row_is_pinned(row)
    return None


async def _set_pin(page, name_or_number: str, pin: bool, wait: float = 2.5) -> dict:
    """Shared implementation for pin_chat / unpin_chat.

    Returns {status, action, name_or_number, already}.
    """
    await open_chat(page, name_or_number, wait)

    # Check current pin state from the sidebar row. WA shows the same chat
    # we just opened highlighted at the top, so the row should be visible.
    # Scroll the sidebar to top first for a reliable read.
    await _scroll_chat_list_to_top(page)
    current = await _is_pinned_in_sidebar(page, name_or_number)
    if current is pin:
        logger.info(
            "%s is already %s",
            name_or_number,
            "pinned" if pin else "unpinned",
        )
        return {
            "status": "noop",
            "action": "pin" if pin else "unpin",
            "name_or_number": name_or_number,
            "already": True,
        }

    # Open header menu.
    opened = await page.evaluate(_OPEN_HEADER_MENU_JS)
    if not opened:
        raise RuntimeError("Couldn't open the chat header menu.")
    ok = await _wait_for(page, _HEADER_MENU_OPEN_JS, timeout_s=wait)
    if not ok:
        raise RuntimeError("The chat header menu didn't render in time.")

    # Click the pin/unpin item. Patterns cover English + Indonesian labels.
    patterns = (
        [r"^pin\s*chat$", r"^pin$", r"^sematkan( chat)?$"]
        if pin
        else [r"^unpin\s*chat$", r"^unpin$", r"^lepas\s*sematan$", r"^batal\s*sematan$"]
    )
    label = await page.evaluate(_CLICK_MENU_ITEM_JS, patterns)
    if not label:
        await _close_any_popup(page)
        raise RuntimeError(f"Couldn't find a {'Pin' if pin else 'Unpin'} option in the chat menu.")

    # Pin cap (3 max) surfaces as a confirm dialog — dismiss anything in the
    # way and re-check sidebar state.
    await asyncio.sleep(0.3)
    # If a confirm dialog appeared, try to press its primary action.
    await page.evaluate(
        """() => {
            const d = document.querySelector('div[role="dialog"]');
            if (!d) return false;
            const btns = [...d.querySelectorAll('[role="button"], button')];
            const prefer = /^(ok|confirm|pin|unpin|sematkan|lepas)/i;
            for (const b of btns) {
                const t = (b.getAttribute('aria-label') || b.innerText || '').trim();
                if (prefer.test(t)) { b.click(); return true; }
            }
            return false;
        }"""
    )

    # Verify new state by re-reading the sidebar row.
    await asyncio.sleep(0.2)
    await _scroll_chat_list_to_top(page)
    new_state = await _is_pinned_in_sidebar(page, name_or_number)
    final = bool(new_state) if new_state is not None else pin
    logger.info("%s chat %r", "Pinned" if final else "Unpinned", name_or_number)
    return {
        "status": "pinned" if final else "unpinned",
        "action": "pin" if pin else "unpin",
        "name_or_number": name_or_number,
        "already": False,
    }


async def pin_chat(page, name_or_number: str, wait: float = 2.5) -> dict:
    """Pin a chat in the sidebar. WA Web allows at most 3 pinned chats."""
    return await _set_pin(page, name_or_number, pin=True, wait=wait)


async def unpin_chat(page, name_or_number: str, wait: float = 2.5) -> dict:
    """Unpin a chat in the sidebar."""
    return await _set_pin(page, name_or_number, pin=False, wait=wait)


async def send_message(page, name_or_number: str, message: str, wait: float = 2.5) -> bool:
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
    # Wait until the composer clears (message dispatched) instead of sleeping.
    await _wait_for(page, _COMPOSER_EMPTY_JS, timeout_s=wait)
    logger.info("Message sent to %r", name_or_number)
    return True


_READ_MESSAGES_JS = r"""
(count) => {
    // WA Web messages carry data-pre-plain-text="[time, date] Sender: " on
    // a span wrapping the message bubble content. We walk up to the row
    // to detect direction via .message-in / .message-out classes.
    const metaRe = /^\[([^\],]+),\s*([^\]]+)\]\s*(.+?):\s*$/;
    const nodes = Array.from(document.querySelectorAll('[data-pre-plain-text]'));
    const result = [];
    for (const el of nodes) {
        const meta = el.getAttribute('data-pre-plain-text') || '';
        const m = meta.match(metaRe);
        if (!m) continue;  // skip list-item / quote fragments
        let dir = 'unknown';
        let anc = el;
        for (let i = 0; i < 12 && anc; i++) {
            if (anc.classList?.contains('message-in')) { dir = 'in'; break; }
            if (anc.classList?.contains('message-out')) { dir = 'out'; break; }
            anc = anc.parentElement;
        }
        const text = (el.innerText || '').trim();
        result.push({
            direction: dir,
            sender: m[3].trim(),
            time: m[1].trim(),
            date: m[2].trim(),
            text,
        });
    }
    return result.slice(-count);
}
"""


async def read_last_messages(page, count: int = 10) -> list[dict]:
    """Read the last visible messages from the currently open chat.

    Returns a list of dicts: {direction, sender, time, date, text}.
    - direction: "in" (received) / "out" (sent by me) / "unknown"
    - sender / time / date parsed from WA's data-pre-plain-text meta.
    """
    return await page.evaluate(_READ_MESSAGES_JS, count)


async def read_last_messages_text(page, count: int = 10) -> list[str]:
    """Backward-compatible variant: return just the text of each message."""
    msgs = await read_last_messages(page, count)
    return [m["text"] for m in msgs]


async def last_incoming_message(page, name_or_number: str) -> dict | None:
    """Open a chat and return the last *received* (incoming) message.

    Returns None if the chat has no incoming messages on screen.
    """
    await open_chat(page, name_or_number)
    # read_last_messages returns chronological order; incoming = direction "in".
    msgs = await read_last_messages(page, count=50)
    for m in reversed(msgs):
        if m["direction"] == "in":
            return m
    return None


async def last_message(page, name_or_number: str) -> dict | None:
    """Open a chat and return the very last message (any direction)."""
    await open_chat(page, name_or_number)
    msgs = await read_last_messages(page, count=5)
    return msgs[-1] if msgs else None
