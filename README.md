# Lazuardy Tech Skills

A collection of AI agent skills for [Lazuardy Tech](https://lazuardy.tech).

## Skills

| Skill | Description |
|-------|-------------|
| [whatsapp-web](./whatsapp-web/) | WhatsApp Web automation (login, chat, number verification) |

## Structure

```
skills/
├── whatsapp-web/                    # WhatsApp Web automation skill
│   ├── src/                         # Python package
│   │   ├── __init__.py              #   WhatsAppWeb facade class
│   │   ├── browser.py               #   Chrome lifecycle + CDP connection
│   │   ├── session.py               #   Login detection & navigation
│   │   ├── chat.py                  #   Send/read messages
│   │   ├── contacts.py              #   Contact search & number verification
│   │   ├── phone.py                 #   Phone number formatting utilities
│   │   └── errors.py                #   Custom exceptions
│   ├── requirements.txt             # Python dependencies
│   └── README.md
├── ...                              # More skills to come
└── README.md
```

Each skill is a self-contained directory with its own `src/`, dependencies, and documentation.

## Adding a New Skill

1. Create a new directory (e.g., `google-sheet/`).
2. Put source code in `src/` inside the skill directory.
3. Include a `README.md` describing purpose, setup, and usage.
4. Add the skill to the table above.

## License

Proprietary - Lazuardy Tech
