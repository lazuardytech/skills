"""Group creation on WhatsApp Web."""

import asyncio
import logging

from .contacts import _wait_for, close_search

logger = logging.getLogger("src.groups")

# JS: click the "New group" entry in the New Chat dialog.
_CLICK_NEW_GROUP_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"], #app > div > div > div');
    const scope = dialog || document;
    const targets = [...scope.querySelectorAll(
        '[role="button"], button, [aria-label], [role="listitem"]'
    )];
    const want = /^(new group|grup baru|grup baru$|buat grup)$/i;
    for (const el of targets) {
        const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
        if (want.test(label)) { el.click(); return true; }
        const firstLine = (el.innerText || '').trim().split('\n')[0];
        if (want.test(firstLine)) { el.click(); return true; }
    }
    return false;
}
"""

# JS: true once the Add members step is visible — it shows a search input
# and a selectable list of contacts/suggestions.
_ADD_MEMBERS_READY_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]') || document;
    const searchBox = dialog.querySelector(
        'input[aria-label*="search" i], input[placeholder*="search" i], '
        + 'input[aria-label*="cari" i], div[contenteditable="true"][role="textbox"]'
    );
    const options = dialog.querySelectorAll('[role="listbox"] [role="option"], '
        + 'div[role="listitem"]');
    return !!searchBox && options.length > 0;
}
"""

# JS: focus the member search input inside the add-members step.
_FOCUS_MEMBER_SEARCH_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]') || document;
    const box = dialog.querySelector(
        'input[aria-label*="search" i], input[placeholder*="search" i], '
        + 'input[aria-label*="cari" i], div[contenteditable="true"][role="textbox"]'
    );
    if (!box) return false;
    box.focus();
    return true;
}
"""

# JS: true once a contact suggestion matching the current query is ready to
# click (i.e. the first option exists and isn't an empty placeholder).
_MEMBER_SUGGESTION_READY_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]') || document;
    const options = dialog.querySelectorAll(
        '[role="listbox"] [role="option"], [role="listbox"] [role="listitem"], '
        + 'div[role="listitem"]'
    );
    for (const opt of options) {
        const text = (opt.innerText || '').trim();
        if (text && !/no result|tidak ada hasil/i.test(text)) return true;
    }
    return false;
}
"""

# JS: detect whether the search returned "no match" for the current query.
_MEMBER_NO_MATCH_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]') || document;
    const text = (dialog.innerText || '').toLowerCase();
    return /no (contacts|results?) found|tidak ada hasil|tidak ditemukan/.test(text);
}
"""

# JS: click the Next / arrow-forward button to proceed from the add-members
# step to the group-subject step.
_CLICK_NEXT_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]') || document;
    const btns = [...dialog.querySelectorAll('[role="button"], button, [aria-label]')];
    // Try explicit labels first.
    const want = /^(next|lanjut|berikutnya|done|selesai)$/i;
    for (const el of btns) {
        const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
        if (want.test(label)) { el.click(); return label || 'next'; }
    }
    // WA often uses an icon-only arrow-forward with aria-label "Next" or a
    // span with data-icon="arrow-forward".
    const icon = dialog.querySelector('[data-icon="arrow-forward"], [data-icon="forward"]');
    if (icon) {
        const clickable = icon.closest('[role="button"], button') || icon;
        clickable.click();
        return 'icon:forward';
    }
    return null;
}
"""

# JS: true once the group-subject step is visible — it has an editable
# subject field (contenteditable div or text input with group/subject hint).
_SUBJECT_STEP_READY_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]') || document;
    const fields = [...dialog.querySelectorAll(
        'div[contenteditable="true"], input[type="text"]'
    )];
    for (const f of fields) {
        const label = (f.getAttribute('aria-label') || f.getAttribute('placeholder')
            || f.getAttribute('title') || '').toLowerCase();
        if (/group (subject|name)|subject|nama grup|subjek/.test(label)) return true;
    }
    // Fallback: any visible contenteditable in a dialog post add-members.
    return fields.length >= 1;
}
"""

# JS: focus the group-subject editor.
_FOCUS_SUBJECT_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]') || document;
    const fields = [...dialog.querySelectorAll(
        'div[contenteditable="true"], input[type="text"]'
    )];
    // Prefer one whose label references group/subject.
    for (const f of fields) {
        const label = (f.getAttribute('aria-label') || f.getAttribute('placeholder')
            || f.getAttribute('title') || '').toLowerCase();
        if (/group (subject|name)|subject|nama grup|subjek/.test(label)) {
            f.focus();
            return true;
        }
    }
    if (fields[0]) { fields[0].focus(); return true; }
    return false;
}
"""

# JS: click the Create button to finalize. Matches English + Indonesian.
_CLICK_CREATE_JS = r"""
() => {
    const dialog = document.querySelector('div[role="dialog"]') || document;
    const btns = [...dialog.querySelectorAll('[role="button"], button, [aria-label]')];
    const want = /^(create( group)?|buat( grup)?|selesai|done)$/i;
    for (const el of btns) {
        const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
        if (want.test(label) && el.getAttribute('aria-disabled') !== 'true'
            && !el.hasAttribute('disabled')) {
            el.click();
            return label || 'create';
        }
    }
    // Fallback: check-mark icon used as "create" confirmation.
    const icon = dialog.querySelector(
        '[data-icon="checkmark"], [data-icon="check"], [data-icon="check-bold"]'
    );
    if (icon) {
        const clickable = icon.closest('[role="button"], button') || icon;
        clickable.click();
        return 'icon:check';
    }
    return null;
}
"""


async def _add_single_member(page, query: str, wait: float) -> bool:
    """Type a query into the member search, pick the first suggestion.

    Returns True on successful add, False if no contact matched.
    """
    focused = await page.evaluate(_FOCUS_MEMBER_SEARCH_JS)
    if not focused:
        return False

    # Clear any existing query, then type.
    await page.keyboard.press("Meta+A")
    await page.keyboard.press("Delete")
    await page.keyboard.type(query)

    # Wait for a suggestion to render OR a no-match state.
    ready = await _wait_for(page, _MEMBER_SUGGESTION_READY_JS, timeout_s=wait)
    if not ready:
        no_match = await page.evaluate(_MEMBER_NO_MATCH_JS)
        if no_match:
            return False

    # Select the first suggestion. Enter is the most reliable path — WA's
    # member picker keeps focus on the input, with the first option
    # highlighted by default.
    await page.keyboard.press("Enter")
    # Small settle for the chip to render.
    await asyncio.sleep(0.15)
    return True


async def create_group(
    page,
    name: str,
    members: list[str],
    wait: float = 3.0,
) -> dict:
    """Create a new WhatsApp group.

    Args:
        name: The group subject/name.
        members: Names or phone numbers to invite. Each is added in turn.
        wait: Per-step timeout.

    Returns:
        {status, name, requested_members, added, failed}.
    """
    added: list[str] = []
    failed: list[str] = []

    # 1. Open New Chat dialog.
    await page.keyboard.press("Meta+Control+n")
    await asyncio.sleep(0.3)

    # 2. Click "New group".
    clicked = await page.evaluate(_CLICK_NEW_GROUP_JS)
    if not clicked:
        await asyncio.sleep(0.4)
        clicked = await page.evaluate(_CLICK_NEW_GROUP_JS)
    if not clicked:
        await close_search(page)
        raise RuntimeError(
            "Couldn't find the 'New group' option in WhatsApp Web. "
            "The dialog layout may have changed."
        )

    # 3. Wait for add-members step.
    ok = await _wait_for(page, _ADD_MEMBERS_READY_JS, timeout_s=wait)
    if not ok:
        await close_search(page)
        raise RuntimeError("The Add members step didn't render in time.")

    # 4. Add each member.
    for member in members:
        member = member.strip()
        if not member:
            continue
        try:
            success = await _add_single_member(page, member, wait=wait)
        except Exception as exc:
            logger.warning("Failed to add %r: %s", member, exc)
            success = False
        if success:
            added.append(member)
        else:
            failed.append(member)

    if not added:
        await close_search(page)
        raise RuntimeError(
            "Couldn't add any members to the group. Check that the names or "
            "numbers match existing contacts."
        )

    # 5. Click Next / arrow-forward to move to the subject step.
    next_label = await page.evaluate(_CLICK_NEXT_JS)
    if not next_label:
        await asyncio.sleep(0.3)
        next_label = await page.evaluate(_CLICK_NEXT_JS)
    if not next_label:
        raise RuntimeError("Couldn't advance to the group-subject step.")

    # 6. Wait for subject step, fill, and create.
    ok = await _wait_for(page, _SUBJECT_STEP_READY_JS, timeout_s=wait)
    if not ok:
        raise RuntimeError("The group-subject step didn't render in time.")

    focused = await page.evaluate(_FOCUS_SUBJECT_JS)
    if not focused:
        raise RuntimeError("Couldn't focus the group-subject field.")
    await page.keyboard.press("Meta+A")
    await page.keyboard.press("Delete")
    await page.keyboard.type(name)
    # Tiny settle so the Create button un-disables.
    await asyncio.sleep(0.2)

    created = await page.evaluate(_CLICK_CREATE_JS)
    if not created:
        await asyncio.sleep(0.3)
        created = await page.evaluate(_CLICK_CREATE_JS)
    if not created:
        raise RuntimeError(
            "Couldn't click Create on the group-subject step. The button may still be disabled."
        )

    # Wait for the dialog to dismiss as the final confirmation.
    await _wait_for(
        page,
        "() => !document.querySelector('div[role=\"dialog\"]')",
        timeout_s=wait,
    )

    logger.info("Created group %r with %d member(s)", name, len(added))
    return {
        "status": "created",
        "name": name,
        "requested_members": members,
        "added": added,
        "failed": failed,
    }
