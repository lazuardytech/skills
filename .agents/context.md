# Project Context

## Overview

AI agent skills by [Lazuardy Tech](https://lazuardy.tech).
Install: `npx skills add lazuardytech/skills --skill <name>`

## Available Skills

| Skill | Description |
|-------|-------------|
| `hive` | Subagent orchestration — 7 agents, parallel execution, Ponytail Ultra |
| `whatsapp-web` | WhatsApp Web automation via Playwright + Chrome CDP |
| `google-sheets` | Google Sheets read/write via gspread |

## Script Conventions

- Output: JSON to stdout, diagnostics to stderr
- Exit codes: `0` success · `1` error · `2` not found · `3` missing `--confirm`
- Destructive scripts require `--confirm` — ask user first
- PEP 723 inline deps — run with `uv run`

## Python Style

- Formatter/linter: Ruff
- Line length: 100
- Target: Python 3.10+
- Run before push:
  ```bash
  ruff format skills/<skill>/
  ruff check skills/<skill>/
  ```

## Adding a Skill

1. Create `skills/<name>/`
2. Add `SKILL.md` with frontmatter (`name`, `description`)
3. Add `README.md`
4. Update table in `README.md`
