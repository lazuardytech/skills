# AGENTS.md

Instructions for AI agents working in this repository.

## Context

Read `.agents/context.md` for project overview, structure, and conventions.

## Working with Skills

- Each skill lives in `skills/<name>/` with its own `SKILL.md`, `scripts/`, `src/`, and `README.md`
- Read the skill's `SKILL.md` before invoking any script — it contains trigger rules and behavioral instructions
- Scripts are non-interactive: pass all inputs as CLI flags
- Always check exit codes and parse JSON stdout for results

## Code Changes

- Match existing style — Ruff, line length 100, Python 3.10+
- Run `ruff format` and `ruff check` on any modified skill before finishing
- Do not add a top-level `requirements.txt` — use PEP 723 inline deps in each script

## Adding a Skill

Follow the steps in `.agents/context.md` → "Adding a New Skill".
After adding, update the skills table in `README.md`.

## Safety

- Destructive scripts (`delete_group.py`, `exit_group.py`, `delete_chat.py`) require `--confirm`
- Always ask the user for explicit confirmation before passing `--confirm`
- Never kill the Chrome process — it persists across runs by design
