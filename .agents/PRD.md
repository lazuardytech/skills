# Product Requirements Document: lazuardytech/skills

**Status**: Active Development · **License**: MIT · **Owner**: Lazuardy Tech

---

## 1. Vision

A curated collection of high-quality, reusable AI agent skills that extend
coding agents (Claude Code, Pi, Command Code, etc.) with domain-specific
capabilities. Each skill is minimal, well-tested, and follows a consistent
architecture — installable in one command, usable immediately.

---

## 2. Target Users

- **AI agent users** who want specialized capabilities (WhatsApp automation,
  Google Sheets access, subagent orchestration) inside their coding agent
- **Developers** building their own agent workflows who need building blocks
- **Lazuardy Tech team** — internal productivity via agent-powered automation

---

## 3. Current Skills

### 3.1 Hive — Subagent Orchestration Framework

**Priority**: P0 · **Status**: Active

Hive Mind turns the main agent into a Senior Lead Software Engineer who
delegates all work to 7 specialized subagents running in parallel.

**Features:**
- 7 subagent roles: explore, plan, executor, auditor, verifier, documenter, operator
- Ponytail Ultra (extreme YAGNI minimalism) baked into every agent
- Parallel execution (3-5 agents simultaneously, max 4 depth)
- Todo-driven orchestration for complex tasks
- Auto-project analysis on activation (up to 12 parallel explore agents)
- Harness-agnostic: supports Command Code, OpenCode, Mistral Vibe, Pi

**Required Pi packages:**
- `@tintinweb/pi-subagents` — Agent tool for spawning subagents
- `@tintinweb/pi-tasks` — TaskCreate/List/Get/Update/Execute for orchestration

### 3.2 WhatsApp Web — Automation Toolkit

**Priority**: P0 · **Status**: Active

WhatsApp Web automation via Playwright + Chrome CDP. Keyboard-driven DOM
interaction for resilience against WA Web DOM changes.

**Features:**
- Login with persistent Chrome session (QR scan once, never re-login)
- Send/read messages with structured output (direction, sender, time, text)
- Chat list introspection (all, pinned, unread with counts)
- Contact management (add, search, verify numbers)
- Group management (create, exit, full teardown)
- Number verification (single and batch)
- Pin/unpin, delete chat, delete group

**14 scripts**, all using PEP 723 inline deps, JSON output, exit codes.

### 3.3 Google Sheets — Read/Write Toolkit

**Priority**: P1 · **Status**: Active

Google Sheets CRUD operations via gspread + Sheets API.

**Features:**
- Read all rows (dict, first row = headers)
- List worksheets (title, rows, cols)
- Update cell (1-indexed row/col), range (A1 notation), or batch
- Append row

**Known gaps:** No delete row, create/delete worksheet, find/replace, formatting.

---

## 4. Roadmap

### Q3 2026
| Item | Status |
|------|--------|
| Pi as first-class harness for Hive | ✅ Done |
| Auto-install Pi packages on `/hive setup` | ✅ Done |
| Drop Mastra Code + hive-setup consolidation | ✅ Done |
| `.agents/` docs refresh (INDEX.md, PRD, context.md) | ✅ Done |

### Future
| Item | Priority |
|------|----------|
| google-sheets: add delete row, create/delete worksheet | P2 |
| google-sheets: add find/replace | P3 |
| whatsapp-web: implement referenced but missing scripts (get_profile, download_media, logout) | P2 |
| hive: custom agent types via `.pi/agents/<name>.md` | P1 |
| hive: Mistral Vibe setup flow (currently detected but partial) | P2 |
| New skill: web research / scraping | P3 |
| New skill: file format conversion (CSV, JSON, Markdown) | P3 |

---

## 5. Technical Requirements

### Script Standards
- JSON to stdout, diagnostics to stderr
- Exit codes: 0 success, 1 error, 2 not found, 3 missing `--confirm`
- PEP 723 inline deps with `requires-python = ">=3.10"`
- `sys.path.insert(0,)` for local imports

### Python Style
- Ruff: line-length 100, double quotes, spaces
- Enabled rules: E, F, I, UP, B, W (explicit E501 waived)
- Target: Python 3.10+

### Safety
- Destructive scripts MUST require `--confirm`
- Agent MUST ask user before passing `--confirm`
- Chrome/WhatsApp session: never kill Chrome
- Credentials: never echo, ensure `.gitignore` protects them

### Hive Architecture
- Agent spawning depth: max 4 levels
- Parallel batching: 3-5 agents, up to 12 for auto-analysis
- Main Agent is sole communicator with user
- Subagent results must be synthesized (never raw)
- Ponytail Ultra is mandatory, not optional

---

## 6. Non-Goals

- **Not a general-purpose agent framework** — Hive is opinionated for code
  work, not a generic agent builder
- **Not a SaaS** — these are CLI/agent skills, not cloud services
- **No persistence layer** — Hive state is session-scoped
- **No WASM or browser automation beyond Playwright** — Chrome CDP only
- **No AI model hosting** — skills use the host agent's existing model access
