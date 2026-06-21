# skills

AI agent skills by [Lazuardy Tech](https://lazuardy.tech).

## Install

```bash
npx skills add lazuardytech/skills --skill <name>
```

## Skills

| Skill | Description |
|-------|-------------|
| [hive](./skills/hive/) | Subagent orchestration — 7 agents, parallel execution, Ponytail Ultra built-in |
| [whatsapp-web](./skills/whatsapp-web/) | WhatsApp Web automation — login, send/read messages, list chats |
| [google-sheets](./skills/google-sheets/) | Google Sheets read/write — read rows, update cells, append rows |

## Structure

```
skills/
  <name>/
    SKILL.md       # Agent triggers + instructions
    README.md      # Human docs
    scripts/       # CLI entry points (optional)
    src/           # Python package (optional)
    prompts/       # Agent prompt files (optional, e.g. hive)
```

## Adding a Skill

1. Create `skills/<name>/`
2. Add `SKILL.md` with frontmatter (`name`, `description`)
3. Add `README.md`
4. Update table above

## Development

```bash
ruff format skills/<skill>/
ruff check skills/<skill>/
```

## License

MIT
