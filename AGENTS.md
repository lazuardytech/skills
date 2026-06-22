# AGENTS.md

Instructions for AI agents working in this repository.

## Context

Read these files in order:

1. `.agents/context.md` — project overview, conventions, architecture
2. `.agents/PRD.md` — product requirements, roadmap, technical standards
3. `.agents/INDEX.md` — directory map of all `.agents/` files

## Skills

- Each skill lives in `skills/<name>/` with `SKILL.md`
- Read `SKILL.md` before invoking any script
- Scripts: JSON to stdout, diagnostics to stderr
- Exit codes: `0` success, `1` error, `2` not found, `3` missing `--confirm`

## Code Changes

- Match existing style: Ruff, line length 100, Python 3.10+
- Run `ruff format` and `ruff check` before push
- Use PEP 723 inline deps, no top-level `requirements.txt`

## Adding a Skill

1. Create `skills/<name>/`
2. Add `SKILL.md` with frontmatter
3. Add `README.md`
4. Update table in `README.md`

## Safety

- Destructive scripts require `--confirm`
- Ask user before passing `--confirm`
- Never kill Chrome process — persists by design
- Never echo `credentials.json` contents
