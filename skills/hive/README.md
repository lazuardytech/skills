# ✦ Hive Mind

Subagent orchestration for Command Code CLI. Spawns a Senior Lead Software Engineer who coordinates 7 specialized subagents for discovery, planning, implementation, review, and verification — all running Ponytail Ultra by default.

## Features

- **7 Subagents** — explore, plan, executor, auditor, verifier, documenter, operator
- **Ponytail Ultra Built-in** — YAGNI-first, minimal solutions, no over-engineering
- **Parallel Execution** — 3-5 agents simultaneously for efficiency
- **Todo-Driven Orchestration** — complex tasks tracked with todos
- **Auto-Project Analysis** — scans repo structure on activation (up to 12 agents)
- **Harness Compatibility** — Command Code CLI only

## Install

```bash
npx skills add https://github.com/lazuardytech/skills --skill hive
```

Then run setup:

```
/hive setup
```

This creates agent prompt files at `~/.commandcode/hive/`.

## Usage

```
/hive          # Activate Hive Mind
/hive on       # Activate Hive Mind
/hive off      # Deactivate
/hive setup    # Verify subagents & create prompt files
```

## How It Works

1. Activate with `/hive`
2. Auto-detects if current directory is a repo
3. Analyzes project structure (parallel explore agents)
4. Delegates all tasks to appropriate subagents
5. Never performs tasks directly — always uses subagent tools

## Subagents

| Agent | Role | Tool |
|-------|------|------|
| explore | Codebase exploration & discovery | `explore` |
| plan | Architecture & implementation planning | `plan` |
| executor | Code changes, shell commands, file ops | `executor` |
| auditor | Code review, security, risk audit | `auditor` |
| verifier | Tests, lint, typecheck, validation | `verifier` |
| documenter | Documentation updates | `documenter` |
| operator | Git, PR, branch, deployment | `operator` |

## Ponytail Ultra

All subagents run Ponytail Ultra by default:

- **YAGNI extremist** — Deletion before addition
- **The ladder** — Stop at first rung that holds
- **No unrequested abstractions**
- **No boilerplate**
- **Shortest working diff wins**

## Structure

```
skills/hive/
├── SKILL.md           # Main skill definition
├── README.md          # This file
├── agents/            # Agent prompt templates (base)
│   ├── discovery.md
│   ├── documentation.md
│   ├── implementation.md
│   ├── operations.md
│   ├── planning.md
│   ├── review.md
│   └── verification.md
└── templates/         # Harness-specific templates
    ├── commandcode/   # Command Code CLI
    ├── opencode/      # OpenCode (markdown with frontmatter)
    ├── mastracode/    # Mastra Code
    └── mistral-vibe/  # Mistral Vibe (TOML + MD)
```

## License

MIT — Copyright (c) 2024–2026 Lazuardy Technology and contributors.
