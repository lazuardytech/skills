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


# JS: locate the "New contact" button in the New Chat dialog, click it.
# Matches English + Indonesian labels; falls back to aria-label scan.
_CLICK_NEW_CONTACT_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"], #app > div > div > div');
    const scope = dialog || document;
    const targets = [...scope.querySelectorAll(
        '[role="button"], button, [aria-label], [role="listitem"]'
    )];
    const want = /^(new contact|kontak baru|tambah kontak)$/i;
    for (const el of targets) {
        const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
        if (want.test(label)) { el.click(); return true; }
        // Some WA builds nest the label text in a child span.
        const text = (el.innerText || '').trim().split('\n')[0];
        if (want.test(text)) { el.click(); return true; }
    }
    return false;
}
"""

# JS: true once the New Contact form is visible (has inputs for name + phone).
_NEW_CONTACT_FORM_READY_JS = r"""
() => {
    const inputs = document.querySelectorAll(
        'div[role="dialog"] input, div[contenteditable="true"][role="textbox"]'
    );
    // Form has at least 3 editable fields (first name, last name, phone).
    return inputs.length >= 3;
}
"""

# JS: return labeled fields inside the New Contact form so we can target
# them by role rather than positional tabs (more resilient).
_FIND_CONTACT_FIELDS_JS = r"""
() => {
    const out = {};
    const fields = document.querySelectorAll(
        'div[role="dialog"] input, div[role="dialog"] div[contenteditable="true"]'
    );
    const keymap = [
        ['first', /first\s*name|nama\s*depan/i],
        ['last',  /last\s*name|nama\s*belakang/i],
        ['phone', /phone|nomor|number/i],
    ];
    for (const el of fields) {
        const label = (el.getAttribute('aria-label') || el.getAttribute('placeholder')
            || el.getAttribute('title') || '').trim();
        for (const [key, re] of keymap) {
            if (!out[key] && re.test(label)) { out[key] = label; break; }
        }
    }
    return out;
}
"""

# JS: set the "Sync contact to phone" checkbox/toggle to a desired state.
# Returns {found: bool, changed: bool, final: bool}.
_SET_SYNC_TOGGLE_JS = r"""
(desired) => {
    const dialog = document.querySelector('div[role="dialog"]');
    if (!dialog) return {found: false, changed: false, final: false};
    const candidates = [...dialog.querySelectorAll(
        '[role="checkbox"], [role="switch"], input[type="checkbox"]'
    )];
    let target = null;
    for (const el of candidates) {
        const label = (el.getAttribute('aria-label') || '').toLowerCase();
        const parentText = (el.closest('label')?.innerText
            || el.parentElement?.innerText || '').toLowerCase();
        if (/sync.*phone|simpan.*telepon|sinkron.*telepon/.test(label + ' ' + parentText)) {
            target = el;
            break;
        }
    }
    if (!target && candidates.length === 1) target = candidates[0];
    if (!target) return {found: false, changed: false, final: false};
    const checked = target.getAttribute('aria-checked') === 'true'
        || target.checked === true;
    let changed = false;
    if (checked !== desired) {
        target.click();
        changed = true;
    }
    const finalChecked = target.getAttribute('aria-checked') === 'true'
        || target.checked === true;
    return {found: true, changed, final: finalChecked};
}
"""

# JS: click the Save button in the New Contact dialog.
_CLICK_SAVE_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]');
    if (!dialog) return false;
    const btns = [...dialog.querySelectorAll('[role="button"], button')];
    const want = /^(save|simpan)$/i;
    for (const el of btns) {
        const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
        if (want.test(label) && !el.hasAttribute('disabled')
            && el.getAttribute('aria-disabled') !== 'true') {
            el.click();
            return true;
        }
    }
    return false;
}
"""


async def _fill_field(page, placeholder_match: str, value: str) -> bool:
    """Focus a dialog input whose aria-label/placeholder matches, then type value.

    Returns True if a field was matched and filled.
    """
    # Prefer locator because inputs can be <input> or contenteditable divs.
    selectors = [
        f'div[role="dialog"] input[aria-label*="{placeholder_match}" i]',
        f'div[role="dialog"] input[placeholder*="{placeholder_match}" i]',
        f'div[role="dialog"] div[contenteditable="true"][aria-label*="{placeholder_match}" i]',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            await loc.click()
            # Clear any pre-filled content (rare but possible).
            await page.keyboard.press("Meta+A")
            await page.keyboard.press("Delete")
            await page.keyboard.type(value)
            return True
        except Exception:
            continue
    return False


async def add_contact(
    page,
    phone: str,
    first_name: str,
    last_name: str = "",
    sync_to_phone: bool = False,
    wait: float = DEFAULT_SEARCH_WAIT,
) -> dict:
    """Add a new contact via WhatsApp Web's New Chat → New contact flow.

    Returns a dict: {status, first_name, last_name, phone, sync_to_phone}.
    status is "saved" on success; raises on UI errors.
    """
    # 1. Open New Chat dialog.
    await page.keyboard.press("Meta+Control+n")
    await asyncio.sleep(0.3)

    # 2. Click "New contact" entry.
    clicked = await page.evaluate(_CLICK_NEW_CONTACT_JS)
    if not clicked:
        # Some WA builds need a second tick for the dialog to paint options.
        await asyncio.sleep(0.4)
        clicked = await page.evaluate(_CLICK_NEW_CONTACT_JS)
    if not clicked:
        await close_search(page)
        raise RuntimeError(
            "Couldn't find the 'New contact' option in WhatsApp Web. "
            "The dialog layout may have changed."
        )

    # 3. Wait for the form to be ready.
    ok = await _wait_for(page, _NEW_CONTACT_FORM_READY_JS, timeout_s=wait)
    if not ok:
        await close_search(page)
        raise RuntimeError("The New Contact form didn't render in time.")

    # 4. Fill fields. Order: first name, last name, phone.
    filled_first = await _fill_field(page, "first name", first_name)
    if not filled_first:
        # Fall back to focusing the first input in the dialog via Tab.
        await page.keyboard.press("Tab")
        await page.keyboard.type(first_name)

    if last_name:
        filled_last = await _fill_field(page, "last name", last_name)
        if not filled_last:
            await page.keyboard.press("Tab")
            await page.keyboard.type(last_name)

    filled_phone = await _fill_field(page, "phone", phone)
    if not filled_phone:
        # Try Indonesian label fallback, then Tab approach.
        if not await _fill_field(page, "nomor", phone):
            await page.keyboard.press("Tab")
            await page.keyboard.type(phone)

    # 5. Sync-to-phone toggle.
    sync_result = await page.evaluate(_SET_SYNC_TOGGLE_JS, sync_to_phone)

    # 6. Click Save.
    saved = await page.evaluate(_CLICK_SAVE_JS)
    if not saved:
        raise RuntimeError(
            "Couldn't click Save on the New Contact form. "
            "The button may be disabled (invalid phone number?)."
        )

    # Wait for dialog to dismiss.
    await _wait_for(
        page,
        "() => !document.querySelector('div[role=\"dialog\"]')",
        timeout_s=wait,
    )

    logger.info("Added contact %r (%s)", f"{first_name} {last_name}".strip(), phone)
    return {
        "status": "saved",
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "sync_to_phone": bool(sync_result.get("final")) if sync_result else sync_to_phone,
    }
