# Project Context

## Overview

AI agent skills monorepo by [Lazuardy Tech](https://lazuardy.tech).
Published as `lazuardytech/skills` on GitHub. MIT licensed.

Each skill is a self-contained, installable package that endows an AI coding
agent (Claude Code, Pi, etc.) with specialized capabilities — instructions,
trigger patterns, and executable scripts.

**Install**: `npx skills add lazuardytech/skills --skill <name>`

---

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| `hive` | Subagent orchestration framework — 7 roles, parallel execution, Ponytail Ultra built-in. Supports Command Code, OpenCode, Mistral Vibe, and Pi. | Active |
| `whatsapp-web` | WhatsApp Web automation via Playwright + Chrome CDP. 14 Python scripts for messaging, contacts, groups, and chat management. | Active |
| `google-sheets` | Google Sheets read/write via gspread + Sheets API. 6 Python scripts for CRUD operations. | Active |

### Removed Skills

| Skill | Reason |
|-------|--------|
| `hive-setup` | Merged into `hive` — Mastra Code support dropped. Pi auto-installs packages via `/hive setup`. |

---

## Repository Structure

```
skills/
├── <name>/
│   ├── SKILL.md        # Agent triggers + instructions (primary agent entry point)
│   ├── README.md       # Human-facing documentation
│   ├── scripts/        # CLI entry points (Python with PEP 723 inline deps)
│   ├── src/            # Python shared modules (optional)
│   └── templates/      # Harness-specific subagent prompt templates (hive only)
.agents/
├── INDEX.md            # This directory map
├── context.md          # This file — project overview
└── PRD.md              # Product Requirements Document
AGENTS.md               # Agent instructions (repo root)
ruff.toml               # Ruff linter/formatter config
```

---

## Technical Conventions

### Python
- **Formatter/Linter**: Ruff (line-length 100, target py310)
- **Dependencies**: PEP 723 inline `# /// script` headers — no top-level `requirements.txt`
- **Run scripts**: `uv run scripts/<name>.py` or `python3 scripts/<name>.py`
- **Pre-push**: `ruff format skills/<skill>/ && ruff check skills/<skill>/`

### Script Convention
- **Output**: JSON to stdout
- **Diagnostics**: Human-readable messages to stderr
- **Exit codes**: `0` success, `1` error, `2` not found, `3` missing `--confirm`
- **Destructive operations**: require `--confirm` flag — agent must ask user first
- **Idempotency**: skip-if-exists pattern used for setup/install scripts

---

## Hive Mind Architecture

Hive is the most complex skill. It activates a multi-agent orchestration mode:

### 7 Subagent Roles
| Role | Tools | Model Tier | Safety |
|------|-------|------------|--------|
| `explore` | read-only | fast | safe |
| `plan` | read-only | premium | safe |
| `executor` | write + bash | premium | neutral |
| `auditor` | read-only | fast | safe |
| `verifier` | read + bash | fast | neutral |
| `documenter` | write (no bash) | fast | safe |
| `operator` | read + bash | fast | neutral |

### Harness Support
| Harness | Subagent Mechanism | Notes |
|---------|-------------------|-------|
| Command Code | Custom tool names (`explore()`, `plan()`, etc.) | Native support |
| OpenCode | Markdown agent defs with subagent mode | YAML frontmatter in templates |
| Mistral Vibe | TOML configs + system prompt files | Dual-file (config + prompt) |
| Pi | `Agent` tool via `@tintinweb/pi-subagents` | Also uses `@tintinweb/pi-tasks` for todo-driven orchestration |

### Key Patterns
- **Ponytail Ultra built-in**: All agents run in extreme YAGNI mode (the Ladder)
- **Parallel execution**: 3-5 agents simultaneously for independent tasks
- **Todo-driven**: Complex tasks (3+ steps) use task tracking for orchestration
- **Depth limit**: Maximum 4 levels of subagent spawning
- **Main Agent**: Only one who communicates with the user

---

## Adding a New Skill

1. Create `skills/<name>/`
2. Add `SKILL.md` with frontmatter (`name`, `description`, `user-invocable`)
3. Add `README.md` with human docs
4. Add `scripts/` and `src/` as needed
5. Add entry to table in root `README.md`
6. Run `ruff format` and `ruff check` before committing

---

## Safety Rules

- **Read `SKILL.md` before invoking any script** — it contains trigger conditions, argument patterns, and safety notes
- **Destructive scripts require `--confirm`** — always ask the user first, never pass `--confirm` automatically
- **Chrome process persists** (whatsapp-web) — never kill Chrome; it preserves the WhatsApp Web session across invocations
- **Credentials** — `credentials.json` (google-sheets) must be in `.gitignore`; never echo its contents
- **Pi packages** — `@tintinweb/pi-subagents` and `@tintinweb/pi-tasks` are auto-installed by `/hive setup` on Pi harness
