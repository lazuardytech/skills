"""Group creation and deletion on WhatsApp Web."""

import asyncio
import logging

from .chat import _CLICK_MENU_ITEM_JS, _HEADER_MENU_OPEN_JS, _OPEN_HEADER_MENU_JS, open_chat
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


# --- Delete group -----------------------------------------------------------
#
# "Delete" on WhatsApp Web has no single action. For an admin, the fullest
# possible teardown is:
#   1. Kick each non-self member (Group info → hover row → Remove).
#   2. Exit the group (header menu → Exit group).
#   3. Delete the group from the chat list (post-exit menu → Delete group).
#
# WA only exposes Remove to admins, so non-admin callers will skip step 1
# silently and go straight to Exit + Delete.


# JS: open the group info panel by clicking the chat header title area.
# Falls back to the header menu → "Group info" item for resilience.
_OPEN_GROUP_INFO_JS = r"""
() => {
    const main = document.querySelector('#main');
    const header = main?.querySelector('header');
    if (!header) return false;
    // The header title area is the first clickable region with the group name.
    // Heuristic: the first <div role="button"> or the first <div> containing
    // an h1/h2-like title. Click it — WA toggles the info drawer.
    const title = header.querySelector('div[role="button"]') || header;
    title.click();
    return true;
}
"""

# JS: true once the group info drawer is open (participants list visible).
_GROUP_INFO_READY_JS = r"""
() => {
    // Participants list is rendered as a list with role="list" or a set of
    // rows each containing a participant name. Match by aria-label scan.
    const candidates = [...document.querySelectorAll('section, aside, div[role="region"]')];
    for (const c of candidates) {
        const txt = (c.innerText || '').toLowerCase();
        if (/participants?|anggota|peserta/.test(txt)) return true;
    }
    return false;
}
"""

# JS: read non-self participant rows. Returns an array of {index, name}.
# We intentionally read by positional index so the caller can loop by
# repeatedly picking index 0 after each removal (the list shrinks).
_READ_PARTICIPANTS_JS = r"""
() => {
    // Find the participants section: scope heuristic is a region whose
    // inner text mentions "participants" / "anggota" / "peserta".
    const regions = [...document.querySelectorAll('section, aside, div[role="region"], div[data-testid]')];
    let scope = null;
    for (const r of regions) {
        const txt = (r.innerText || '').toLowerCase();
        if (/participants?|anggota|peserta/.test(txt)) { scope = r; break; }
    }
    if (!scope) return {error: 'no participants region'};
    // Participant rows: each row has a clickable area with the member name.
    // Filter out headers/search boxes by requiring a first-line that's not
    // a section label and isn't "you" / "kamu" (self row).
    const rows = [...scope.querySelectorAll('[role="button"], div[role="listitem"], li')];
    const out = [];
    const seen = new Set();
    for (const row of rows) {
        const text = (row.innerText || '').trim();
        if (!text) continue;
        const first = text.split('\n')[0].trim();
        if (!first) continue;
        const low = first.toLowerCase();
        if (/^(participants?|anggota|peserta|search|cari|add participant|tambah)/.test(low)) continue;
        // Self rows are usually marked "You" or "Kamu" somewhere in the row.
        if (/\b(you|kamu)\b/i.test(text)) continue;
        if (seen.has(first)) continue;
        seen.add(first);
        out.push({name: first});
    }
    return {rows: out};
}
"""

# JS: given a member display-name, open that member's row menu and click
# the Remove/Keluarkan item. Returns the clicked label on success.
_REMOVE_MEMBER_JS = r"""
(name) => {
    const regions = [...document.querySelectorAll('section, aside, div[role="region"], div[data-testid]')];
    let scope = null;
    for (const r of regions) {
        const txt = (r.innerText || '').toLowerCase();
        if (/participants?|anggota|peserta/.test(txt)) { scope = r; break; }
    }
    if (!scope) return {error: 'no region'};
    const rows = [...scope.querySelectorAll('[role="button"], div[role="listitem"], li')];
    let target = null;
    for (const row of rows) {
        const first = (row.innerText || '').trim().split('\n')[0].trim();
        if (first === name) { target = row; break; }
    }
    if (!target) return {error: 'row not found'};
    // Click the row to open the member action sheet.
    target.click();
    return {opened: true};
}
"""

# JS: in the member action sheet, click Remove. WA uses a popup menu with
# items like "Message X", "View X", "Remove X", "Make group admin".
_CLICK_REMOVE_ITEM_JS = r"""
(nameHint) => {
    const menus = [...document.querySelectorAll(
        '[role="menu"], div[role="application"], div[role="dialog"]'
    )];
    for (const m of menus) {
        const items = [...m.querySelectorAll('[role="menuitem"], [role="button"], li')];
        for (const el of items) {
            const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
            if (/^remove\s|^keluarkan|^hapus anggota/i.test(label)) {
                el.click();
                return label;
            }
        }
    }
    return null;
}
"""

# JS: click the primary action on a confirm dialog (Remove / Keluarkan /
# Exit / Keluar / Delete / Hapus), returning the label clicked.
_CONFIRM_DIALOG_JS = r"""
(patterns) => {
    const dialog = document.querySelector('div[role="dialog"]');
    if (!dialog) return null;
    const regs = patterns.map(p => new RegExp(p, 'i'));
    const btns = [...dialog.querySelectorAll('[role="button"], button')];
    for (const el of btns) {
        const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
        for (const re of regs) {
            if (re.test(label)) { el.click(); return label; }
        }
    }
    return null;
}
"""


async def _kick_all_members(page, wait: float) -> tuple[list[str], list[str]]:
    """Open group info, loop-remove every non-self member.

    Returns (kicked, skipped). Skipped are rows whose Remove action failed
    (e.g. the caller isn't admin and the option isn't shown).
    """
    # Open info panel.
    await page.evaluate(_OPEN_GROUP_INFO_JS)
    ok = await _wait_for(page, _GROUP_INFO_READY_JS, timeout_s=wait)
    if not ok:
        return [], []

    kicked: list[str] = []
    skipped: list[str] = []
    # Safety cap: WA groups can have 1024 members; we bound iterations so a
    # stuck selector can't spin forever.
    max_iters = 1500
    last_name: str | None = None
    repeat_count = 0

    for _ in range(max_iters):
        data = await page.evaluate(_READ_PARTICIPANTS_JS)
        if "error" in data:
            break
        rows = data.get("rows", [])
        if not rows:
            break

        name = rows[0]["name"]
        # Guard against infinite loop when the same row fails to remove.
        if name == last_name:
            repeat_count += 1
            if repeat_count >= 2:
                skipped.append(name)
                # Try the next row by popping the stuck one from consideration.
                if len(rows) > 1:
                    name = rows[1]["name"]
                    repeat_count = 0
                else:
                    break
        else:
            last_name = name
            repeat_count = 0

        opened = await page.evaluate(_REMOVE_MEMBER_JS, name)
        if not opened or "error" in opened:
            skipped.append(name)
            continue

        await asyncio.sleep(0.2)
        clicked = await page.evaluate(_CLICK_REMOVE_ITEM_JS, name)
        if not clicked:
            # No Remove option surfaced — likely not admin, stop trying.
            await page.keyboard.press("Escape")
            skipped.extend(r["name"] for r in rows if r["name"] not in skipped)
            break

        # Confirm dialog.
        await asyncio.sleep(0.25)
        confirm = await page.evaluate(
            _CONFIRM_DIALOG_JS,
            [r"^remove$", r"^keluarkan$", r"^hapus$", r"^ok$"],
        )
        # Some builds remove without a confirm — that's fine.
        _ = confirm
        await asyncio.sleep(0.4)
        kicked.append(name)

    return kicked, skipped


async def _exit_and_delete_group(page, wait: float) -> dict:
    """From an open group chat, run Exit group → Delete group.

    Returns {exited: bool, deleted: bool}.
    """
    result = {"exited": False, "deleted": False}

    # Close info drawer if it's still open — header menu needs the chat view.
    await page.keyboard.press("Escape")
    await asyncio.sleep(0.2)

    # Open header menu.
    opened = await page.evaluate(_OPEN_HEADER_MENU_JS)
    if not opened:
        raise RuntimeError("Couldn't open the chat header menu for exit.")
    ok = await _wait_for(page, _HEADER_MENU_OPEN_JS, timeout_s=wait)
    if not ok:
        raise RuntimeError("The chat header menu didn't render in time.")

    # Click Exit group. WA Web uses "Exit group" / "Keluar dari grup".
    clicked = await page.evaluate(
        _CLICK_MENU_ITEM_JS,
        [r"^exit\s*group$", r"^keluar(\s*dari)?\s*grup$", r"^exit$"],
    )
    if not clicked:
        # Maybe already exited — fall through to try delete directly.
        logger.info("Exit option not found; trying delete flow directly")
    else:
        await asyncio.sleep(0.3)
        await page.evaluate(
            _CONFIRM_DIALOG_JS,
            [r"^exit$", r"^keluar$", r"^ok$", r"^yes$"],
        )
        result["exited"] = True
        await asyncio.sleep(0.5)

    # Re-open header menu for Delete group. After exit, the composer is
    # gone but the menu still lives on the header.
    opened = await page.evaluate(_OPEN_HEADER_MENU_JS)
    if not opened:
        return result
    await _wait_for(page, _HEADER_MENU_OPEN_JS, timeout_s=wait)
    clicked = await page.evaluate(
        _CLICK_MENU_ITEM_JS,
        [r"^delete\s*group$", r"^hapus\s*grup$", r"^delete\s*chat$", r"^hapus\s*chat$"],
    )
    if not clicked:
        return result

    await asyncio.sleep(0.3)
    await page.evaluate(
        _CONFIRM_DIALOG_JS,
        [r"^delete$", r"^hapus$", r"^ok$", r"^yes$", r"^delete group$", r"^delete chat$"],
    )
    result["deleted"] = True
    await asyncio.sleep(0.4)
    return result


async def exit_group(page, name_or_number: str, wait: float = 3.0) -> dict:
    """Exit (leave) a group without deleting it from the chat list.

    The group stays visible in the sidebar as a read-only conversation and
    remains active for the other members. Returns {status, name, exited}.

    status is "exited" on success, "noop" if the group was already left
    (no Exit option surfaced), or raises on UI errors.
    """
    await open_chat(page, name_or_number, wait)

    # Header menu → Exit group / Keluar dari grup.
    opened = await page.evaluate(_OPEN_HEADER_MENU_JS)
    if not opened:
        raise RuntimeError("Couldn't open the chat header menu for exit.")
    ok = await _wait_for(page, _HEADER_MENU_OPEN_JS, timeout_s=wait)
    if not ok:
        raise RuntimeError("The chat header menu didn't render in time.")

    clicked = await page.evaluate(
        _CLICK_MENU_ITEM_JS,
        [r"^exit\s*group$", r"^keluar(\s*dari)?\s*grup$", r"^exit$"],
    )
    if not clicked:
        # Menu has no Exit item — caller already left.
        await page.keyboard.press("Escape")
        logger.info("exit_group(%r): already left", name_or_number)
        return {
            "status": "noop",
            "name": name_or_number,
            "exited": False,
            "already": True,
        }

    await asyncio.sleep(0.3)
    await page.evaluate(
        _CONFIRM_DIALOG_JS,
        [r"^exit$", r"^keluar$", r"^ok$", r"^yes$", r"^exit group$"],
    )
    await asyncio.sleep(0.4)

    logger.info("Exited group %r", name_or_number)
    return {
        "status": "exited",
        "name": name_or_number,
        "exited": True,
        "already": False,
    }


async def delete_group(page, name_or_number: str, wait: float = 3.0) -> dict:
    """Kick all members, exit the group, delete it from the chat list.

    Returns:
        {status, name, kicked, skipped, exited, deleted}

    status is "deleted" when the group was removed from the chat list,
    "exited" if exit succeeded but delete didn't, or "partial" otherwise.
    kicked/skipped list member names; skipped covers rows where the caller
    isn't admin or the Remove action didn't surface.
    """
    await open_chat(page, name_or_number, wait)

    kicked, skipped = await _kick_all_members(page, wait=wait)
    final = await _exit_and_delete_group(page, wait=wait)

    if final["deleted"]:
        status = "deleted"
    elif final["exited"]:
        status = "exited"
    else:
        status = "partial"

    logger.info(
        "delete_group(%r): status=%s kicked=%d skipped=%d",
        name_or_number,
        status,
        len(kicked),
        len(skipped),
    )
    return {
        "status": status,
        "name": name_or_number,
        "kicked": kicked,
        "skipped": skipped,
        "exited": final["exited"],
        "deleted": final["deleted"],
    }
