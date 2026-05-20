# 📦 skills

A collection of AI agent skills by [Lazuardy Tech](https://lazuardy.tech).

## Install

```bash
# Install a specific skill
npx skills add lazuardytech/skills --skill whatsapp-web

# List available skills
npx skills add lazuardytech/skills --list
```

## Skills

| Skill | Description |
|-------|-------------|
| [whatsapp-web](./skills/whatsapp-web/) | WhatsApp Web automation — login, send/read messages, list chats, count unread, number verification |
| [google-sheets](./skills/google-sheets/) | Google Sheets read/write — read rows, update cells, batch update, append rows, list worksheets |

## Structure

```
├── skills/
│   ├── whatsapp-web/                # WhatsApp Web automation skill
│   │   ├── SKILL.md                 #   Skill metadata, triggers, agent instructions
│   │   ├── README.md                #   Human-facing docs
│   │   ├── scripts/                 #   CLI entry points (agent-callable)
│   │   │   ├── login.py             #     Open WA Web / check login state
│   │   │   ├── check_number.py      #     Verify number(s) on WhatsApp
│   │   │   ├── add_contact.py       #     Add a new contact
│   │   │   ├── send_message.py      #     Send a message
│   │   │   ├── pin_chat.py          #     Pin / unpin a chat
│   │   │   ├── create_group.py      #     Create a new group
│   │   │   ├── delete_group.py      #     Kick all members + exit + delete
│   │   │   ├── exit_group.py        #     Leave a group (keeps in chat list)
│   │   │   ├── delete_chat.py       #     Remove a chat from the sidebar
│   │   │   ├── read_messages.py     #     Read recent messages from a chat
│   │   │   ├── last_reply.py        #     Last incoming reply / last message
│   │   │   ├── list_chats.py        #     List chats in the sidebar
│   │   │   ├── list_pinned.py       #     List pinned chats
│   │   │   └── list_unread.py       #     List unread chats, count unread
│   │   └── src/                     #   Python package used by the scripts
│   │       ├── __init__.py          #     WhatsAppWeb facade class
│   │       ├── browser.py           #     Chrome lifecycle + CDP connection
│   │       ├── session.py           #     Login detection & navigation
│   │       ├── chat.py              #     Send/read messages, chat list, pin/unpin
│   │       ├── contacts.py          #     Contact search, number verification, add contact
│   │       ├── groups.py            #     Group creation + deletion
│   │       ├── phone.py             #     Phone number formatting utilities
│   │       └── errors.py            #     Custom exceptions
│   ├── google-sheets/               # Google Sheets automation skill
│   │   ├── SKILL.md                 #   Skill metadata, triggers, agent instructions
│   │   ├── README.md                #   Human-facing docs
│   │   ├── scripts/                 #   CLI entry points (agent-callable)
│   │   │   ├── read_rows.py         #     Read all rows as list of dicts
│   │   │   ├── list_worksheets.py   #     List all worksheets
│   │   │   ├── update_cell.py       #     Update a single cell
│   │   │   ├── update_range.py      #     Update a named range
│   │   │   ├── batch_update.py      #     Batch-update multiple cells
│   │   │   └── append_row.py        #     Append a row
│   │   └── src/                     #   Python package used by the scripts
│   │       └── __init__.py          #     gspread client + helpers
│   └── ...                          # More skills to come
├── ruff.toml                        # Python formatter/linter config
└── README.md
```

Each skill lives under `skills/` with its own `SKILL.md`, `scripts/`, `src/`, and `README.md`. Scripts use [PEP 723](https://peps.python.org/pep-0723/) inline dependencies, so there is no top-level `requirements.txt`.

## Adding a New Skill

1. Create a new directory under `skills/` (e.g., `skills/google-sheet/`).
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description`, `license`, `compatibility`). The `description` drives agent trigger matching — list the user prompts that should invoke the skill.
3. Put the Python package in `src/`.
4. Add CLI entry points in `scripts/` (one per agent-callable action). Each script should:
   - Declare deps via PEP 723 inline metadata
   - Accept input via CLI flags (non-interactive)
   - Print JSON to stdout, diagnostics to stderr
   - Use exit codes: `0` success, `1` needs login, `2` not found
5. Include a `README.md` describing purpose, setup, and usage.
6. Add the skill to the table above.

## Development

Python code is formatted and linted with [Ruff](https://docs.astral.sh/ruff/) (config in `ruff.toml`, line length 100, py310 target).

```bash
ruff format skills/<skill>/
ruff check skills/<skill>/
```

Run both before every push.

## License

Proprietary - Lazuardy Tech
