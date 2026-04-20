# doit-cc-plugin: Design Document

## Overview

A feature development pipeline plugin for Claude Code. Guides a project from raw idea through
structured PRD → planning → automated execution. Built as slash commands + markdown prompts;
plugin API integration deferred until API stabilizes.

---

## Pipeline Phases

### Phase 1 — Context Preparation

**Step 1 — Input & PRD Generation**

User describes the project in free form (dumps everything they know). Claude organizes it.

- Input in Russian → generate `prd_ru.md` → user confirms → derive `prd.md` from confirmed Russian
- Input in English → generate `prd.md` directly
- `prd_ru.md` is the primary artifact for Russian users; `prd.md` is derived from it
- For English users: only `prd.md` is generated, no Russian versions

**Step 2 — CLAUDE.md**

Permanent per-session context for Claude Code. Contains: tech stack, architectural decisions
already made, code conventions (naming, folder structure), what not to touch, how to run tests.
Stack is auto-detected from CLAUDE.md; if absent, offer to clarify now or defer to interview.

**Step 3 — Detail Clarification (optional)**

If PRD lacks technical detail (stack, architecture) — explicitly offer: clarify now or defer
to interview. User chooses.

---

### Phase 2 — Interview

**Step 4 — Interview Setup**

Before starting, configure mode:
- Question limit: specify number or unlimited
- Chunked mode (recommended): pause every 5 questions and report:
  - Current understanding confidence level
  - Criticality of remaining gaps ("must resolve before coding" vs "can defer")
  - Options: continue 5-10 more / finish interview / model declares ready

Assessment is honest — not "all clear" by default.

**Step 5 — Interview**

Focus: technical tradeoffs, edge cases, architectural decisions, UI/UX, things the user
may have missed. Absorbs questions deferred from Step 3.

Goal: `prd.md` detailed enough that any senior engineer executes without clarification.

After interview: update `prd_ru.md` first (if lang=ru), then regenerate `prd.md` from it.

---

### Phase 3 — Planning

**Step 6 — plan.md (Strategy)**

High-level plan: work order, dependencies, architectural blocks.
Gate: user approval required before proceeding.
Catches errors like: wrong sequence, missing whole modules.
Generates `plan_ru.md` first (if lang=ru), user approves, then `plan.md` derived from it. English users: `plan.md` only.

**Step 7 — implementation_plan.md + implementation_plan.json**

Each block from `plan.md` broken into concrete steps. Gate: user approval required.
Catches errors like: too coarse-grained, unnecessary steps, missing steps.
Generates `implementation_plan_ru.md` first (if lang=ru), user approves, then `implementation_plan.md` derived from it. English users: `implementation_plan.md` only.

JSON is generated immediately after approval — strict mechanical conversion, no interpretation.
If the user later wants to change the plan, they edit `implementation_plan.md` and re-run
this step to regenerate the JSON.

Each task:
```json
{
  "id": "1.1",
  "category": "backend",
  "description": "...",
  "verification": ["npm test -- --grep 'name'", "curl http://localhost:3000/health"],
  "passes": false
}
```

Tasks must fit within one context window. Verification steps are runnable commands.

---

### Phase 4 — Execution

**Step 9 — Supervised run**

```bash
ralph 3   # watch: does it pick tasks correctly, do tests pass?
```

**Step 10 — Full run**

```bash
ralph 10
```

---

### Phase 5 — Control

- At ~40-50% context usage → new session; ralph continues via `progress.md`
- Stuck task → split: Claude proposes subtasks to user, waits for approval before modifying
  `implementation_plan.json`
- `progress.md` and git history → audit of what was done

---

## Key Files

| File | Level | What | Who writes |
|---|---|---|---|
| `prd.md` | requirements | requirements in English | Claude |
| `prd_ru.md` | requirements | requirements in Russian (primary for ru users) | Claude + user confirms |
| `CLAUDE.md` | context | permanent per-session project context | user |
| `plan.md` | strategy | high-level plan, approved | Claude → user approves |
| `plan_ru.md` | strategy | plan in Russian (primary for ru users) | Claude + user confirms |
| `implementation_plan.md` | tactics | detailed steps, approved | Claude → user approves |
| `implementation_plan_ru.md` | tactics | detailed plan in Russian (primary for ru users) | Claude + user confirms |
| `implementation_plan.json` | execution | tasks for ralph | Claude from approved impl plan |
| `progress.md` | runtime | execution log | ralph automatically |
| `.pipeline/state.json` | runtime | pipeline state (gitignored) | pipeline |

---

## Architecture

### Entry Point

`/armchair-architect` — reads state, routes to current step or handles subcommand.

Subcommands via `$ARGUMENTS`:
- `/armchair-architect` — run or continue from current step
- `/armchair-architect status` — show current state
- `/armchair-architect reset` — confirm and clear state
- `/armchair-architect use <component> <impl>` — switch impl (e.g., `use execute ralphex`)

### Two-Level Abstraction

```
/armchair-architect ($ARGUMENTS)
    ↓
SKILL.md orchestrator (reads state.json, selects step)
    ↓
┌──────────────────────────────────┐
│  Level 1: WHAT (steps/)          │
│  step contract — stable          │
│  01_init, 02_interview_setup...  │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│  Level 2: HOW (impl/)            │
│  swappable implementation        │
│  interview/: ask_user_question   │
│  execute/:   ralph, ralphex      │
└──────────────────────────────────┘
```

### State Schema

`.pipeline/state.json` (in user's project, gitignored):

```json
{
  "step": "interview",
  "lang": "ru",
  "interview_mode": "chunked_5",
  "interview_questions_asked": 7,
  "completed": ["prd_draft", "clarify"],
  "pending": ["interview", "plan", "impl_plan", "execute"],
  "impl": {
    "interview": "ask_user_question",
    "execute": "ralph"
  }
}
```

---

## Closed Design Decisions

| Question | Decision | Reason |
|---|---|---|
| Slash command format | `skills/armchair-architect/SKILL.md` | Plugin-compatible; `${CLAUDE_SKILL_DIR}` resolves step paths without hardcoding |
| Subcommands | `$ARGUMENTS` routing in single SKILL.md | No native subcommand support in Claude Code |
| State injection | `` !`cat .pipeline/state.json 2>/dev/null \|\| echo '{}'` `` | Injects live state before Claude sees prompt |
| Ralph call | Claude uses Bash tool | More flexible; can monitor output and react |
| Impl switching | Manual edit of `.pipeline/state.json` | MVP simplicity; no extra command needed |
| Task split | Claude proposes, user approves | Prevents silent scope changes |
| Bilingual sync | At phase boundaries + explicit user command | Avoids drift during long interviews |

---

## Installation

```bash
# Global (available in all projects)
git clone https://github.com/<you>/doit-cc-plugin ~/.claude/plugins/doit-cc-plugin

# Per-project
git clone https://github.com/<you>/doit-cc-plugin .claude/plugins/doit-cc-plugin
```

Configure in `settings.json`:
```json
{ "plugins": ["~/.claude/plugins/doit-cc-plugin"] }
```

Update: `git pull` in plugin directory.

---

## Open Questions (Deferred)

- Plugin-to-plugin invocation patterns once plugin API stabilizes
- Auto-detection of context usage threshold for Phase 5 session handoff
- Ralphex integration (alternative executor)
