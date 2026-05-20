# Project Context

## Overview

A collection of AI agent skills by [Lazuardy Tech](https://lazuardy.tech).
Skills are installable via `npx skills add lazuardytech/skills --skill <name>`.

## Structure

```
skills/
  <name>/
    SKILL.md       # Agent trigger metadata + instructions
    README.md      # Human-facing docs
    scripts/       # CLI entry points (agent-callable, one action per file)
    src/           # Python package used by scripts
.agents/
  INDEX.md         # This directory map
  context.md       # This file
AGENTS.md          # Agent instructions (root)
ruff.toml          # Python formatter/linter config
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `whatsapp-web` | WhatsApp Web automation via Playwright + Chrome CDP |
| `google-sheets` | Google Sheets read/write via Sheets API + gspread |

## Script Conventions

- Output: JSON to stdout, diagnostics to stderr
- Exit codes: `0` success · `1` login required/error · `2` not found · `3` missing `--confirm`
- Destructive scripts require `--confirm` flag — agent must ask user first
- PEP 723 inline deps — run with `uv run` or install Playwright manually
- Phone formatting defaults to Indonesian numbers (+62)

## Python Style

- Formatter/linter: [Ruff](https://docs.astral.sh/ruff/)
- Line length: 100
- Target: Python 3.10+
- Run before every push:
  ```bash
  ruff format skills/<skill>/
  ruff check skills/<skill>/
  ```

## Adding a New Skill

1. Create `skills/<name>/`
2. Add `SKILL.md` with YAML frontmatter (`name`, `description`, `license`, `compatibility`)
3. Put the Python package in `src/`
4. Add CLI entry points in `scripts/` — one file per action
5. Add `README.md` with purpose, setup, and usage
6. Register the skill in the table in `README.md`
