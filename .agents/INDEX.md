# .agents/

Agent-readable documentation for the `lazuardytech/skills` repository.

## Contents

| File | Purpose |
|------|---------|
| `INDEX.md` | This file — directory map |
| `context.md` | Project overview, conventions, architecture, workflow |
| `PRD.md` | Product Requirements Document — vision, scope, roadmap |

## Quick Reference

- **Repo**: AI agent skills by [Lazuardy Tech](https://lazuardy.tech) — MIT licensed
- **Install**: `npx skills add lazuardytech/skills --skill <name>`
- **Skills**: `hive`, `whatsapp-web`, `google-sheets` (see `skills/<name>/`)
- **Python**: Ruff (line-length 100), target py310, PEP 723 inline deps
- **Scripts**: JSON stdout, diagnostics stderr, exit codes 0/1/2/3
- **Destructive ops**: require `--confirm` flag

## Required Reading Order

For new agents, read in this order:

1. `AGENTS.md` (repo root) — agent instructions for this repo
2. `.agents/context.md` — project context, conventions, skills overview
3. `.agents/PRD.md` — product vision and roadmap
4. `README.md` — human-facing project docs
5. `skills/<name>/SKILL.md` — skill-specific instructions (before invoking any skill)
