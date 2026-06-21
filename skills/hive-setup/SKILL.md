---
name: hive-setup
description: >
  Run Hive Mind setup — detects harness and creates agent config files.
  Use when the user says "/hive setup" or "setup hive".
user-invocable: true
---

# Hive Setup

<EXTREMELY-IMPORTANT>
You MUST perform the setup now. Do NOT ask questions. Execute immediately.
</EXTREMELY-IMPORTANT>

## Detect Harness

Check which harness is running:
1. `~/.mastracode/` exists → Mastra Code
2. `~/.commandcode/` exists → Command Code CLI
3. `~/.opencode/` exists → OpenCode
4. `~/.vibe/` exists → Mistral Vibe

## Mastra Code Setup

1. Create `~/.mastracode/skills/hive/` if missing
2. Copy agent prompts from `templates/mastracode/` in the hive skill
3. Report status

## Output Format

```
Hive Mind Setup
═══════════════

Detected Harness: Mastra Code

Step 1: Checking agents...
  explore        ✓ OK
  plan           ✓ OK
  executor       ✓ OK
  auditor        ✓ OK
  verifier       ✓ OK
  documenter     ✓ OK
  operator       ✓ OK

Step 2: Setting up configs...
  ~/.mastracode/skills/hive/agents/discovery.md      ✓ Created
  ~/.mastracode/skills/hive/agents/planning.md       ✓ Created
  ~/.mastracode/skills/hive/agents/implementation.md ✓ Created
  ~/.mastracode/skills/hive/agents/review.md         ✓ Created
  ~/.mastracode/skills/hive/agents/verification.md   ✓ Created
  ~/.mastracode/skills/hive/agents/documentation.md  ✓ Created
  ~/.mastracode/skills/hive/agents/operations.md     ✓ Created

Hive Mind is ready.
```
