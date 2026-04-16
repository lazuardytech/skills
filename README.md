# Lazuardy Tech Skills

A collection of AI agent skills for [Lazuardy Tech](https://lazuardy.tech).

## Install

```bash
# Install specific skill
npx skills add lazuardytech/skills --skill whatsapp-web

# List available skills
npx skills add lazuardytech/skills --list
```

## Skills

| Skill | Description |
|-------|-------------|
| [whatsapp-web](./skills/whatsapp-web/) | WhatsApp Web automation (login, chat, number verification) |

## Structure

```
├── skills/
│   ├── whatsapp-web/                # WhatsApp Web automation skill
│   │   ├── SKILL.md                 #   Skill metadata & instructions
│   │   ├── src/                     #   Python package
│   │   │   ├── __init__.py          #     WhatsAppWeb facade class
│   │   │   ├── browser.py           #     Chrome lifecycle + CDP connection
│   │   │   ├── session.py           #     Login detection & navigation
│   │   │   ├── chat.py              #     Send/read messages
│   │   │   ├── contacts.py          #     Contact search & number verification
│   │   │   ├── phone.py             #     Phone number formatting utilities
│   │   │   └── errors.py            #     Custom exceptions
│   │   ├── requirements.txt         #   Python dependencies
│   │   └── README.md
│   └── ...                          # More skills to come
└── README.md
```

Each skill lives under `skills/` with its own `SKILL.md`, `src/`, dependencies, and documentation.

## Adding a New Skill

1. Create a new directory under `skills/` (e.g., `skills/google-sheet/`).
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description`).
3. Put source code in `src/` inside the skill directory.
4. Include a `README.md` describing purpose, setup, and usage.
5. Add the skill to the table above.

## License

Proprietary - Lazuardy Tech
