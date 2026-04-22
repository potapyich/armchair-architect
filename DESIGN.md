# armchair-architect: Design Document

## Overview

A feature development pipeline plugin for Claude Code. Guides a project from raw idea through
structured PRD → planning → automated execution. Built as markdown prompt files; all logic
is interpreted by Claude Code at runtime with zero external dependencies.

---

## Pipeline Phases

### Phase 1 — Init & Setup

**Step 1 — Init (`01_init.md`)**

User describes the project in free form. Claude generates a structured PRD.

- Input in Russian → generate `prd_ru.md` → user confirms → derive `prd.md` from confirmed Russian
- Input in English → generate `prd.md` directly
- `prd_ru.md` is the primary artifact for Russian users; `prd.md` is derived, not edited directly
- PRD critique runs here if enabled (saves findings to state as `critique_prd` — feeds interview)
- Offer to create `CLAUDE.md` if missing

**Step 2 — Setup (`02_setup.md`)**

Configure pipeline options before interview:
- **context7** — check if installed; offer to add to `~/.claude/settings.json` (requires session restart)
- **Critique mode** — `none` (default) / `default` / `strict`
- **TDD mode** — on/off (requires ralph-loop)
- **Code review gate** — off / every 3 / 5 / 10 tasks

All choices saved to `impl` in state.

---

### Phase 2 — Interview

**Step 3 — Interview Setup (`03_interview_setup.md`)**

Configure interview mode: question limit and chunked vs continuous.

**Step 4 — Interview (`04_interview.md`)**

Targeted questions to fill PRD gaps. Starts from `critique_prd` findings if available.
After interview: update `prd_ru.md` first (if lang=ru), then regenerate `prd.md` from it.

---

### Phase 3 — Planning

**Step 5 — Plan (`05_plan.md`)**

High-level work blocks with dependencies. Gate: user approval required.
Generates `plan_ru.md` first (if lang=ru), user approves, then `plan.md` derived from it.

**Step 6 — Implementation Plan (`06_impl_plan.md`)**

Each block broken into concrete steps with acceptance criteria. Gate: user approval required.
Implementation plan critique runs here if enabled (shown alongside approval gate).
JSON generated immediately after approval — strict mechanical conversion, no interpretation.

Generates `implementation_plan_ru.md` first (if lang=ru), user approves, then `implementation_plan.md` and `implementation_plan.json` derived from it.

---

### Phase 4 — Execution

**Step 7 — Execute (`07_execute.md`)**

Reads `impl.execute` from state. Loads the corresponding impl file. Default: built-in executor.

User chooses how many tasks to run (3 / all / N).

The built-in executor (`impl/execute/default.md`):
- Finds ready tasks (passes: false, all dependsOn satisfied)
- Parallel groups: tasks with `parallel: true` + same `group` → launched via Agent tool simultaneously; results merged from `task_<id>_result.json` temp files
- Per-task: mark `in_progress: true` → implement → verify → mark `passes: true` / stuck
- Stuck task options: split / skip / stop / **escalate to plan** (writes `escalation.md`, rolls back state)
- Code review gate: every N tasks → subagent reviews `git diff HEAD~N`, user approves before continuing
- Context handoff: at ~40-50% usage → write `progress.md`, suggest new session

For ralph-loop (`impl/execute/ralph.md`):
- Tell user to run `/ralph-loop` in a new session
- ralph reads `implementation_plan.json` and executes from first `passes: false` task
- After ralph completes: run `/armchair-architect` to sync and continue

---

## Key Files

| File | Level | What | Who writes |
|---|---|---|---|
| `prd.md` | requirements | PRD in English (canonical) | Claude |
| `prd_ru.md` | requirements | PRD in Russian (primary for ru users) | Claude + user confirms |
| `plan.md` | strategy | High-level plan, English | Claude |
| `plan_ru.md` | strategy | High-level plan, Russian (primary for ru users) | Claude + user confirms |
| `implementation_plan.md` | tactics | Detailed steps, English | Claude |
| `implementation_plan_ru.md` | tactics | Detailed steps, Russian (primary for ru users) | Claude + user confirms |
| `implementation_plan.json` | execution | Tasks for executor | Claude (from approved impl plan) |
| `progress.md` | runtime | Written on context handoff — done/remaining task list | Executor |
| `escalation.md` | runtime | Written when a task reveals a plan-level problem | Executor |
| `.pipeline/active` | runtime | Name of the active pipeline | Pipeline |
| `.pipeline/<feature>/state.json` | runtime | Pipeline state (gitignored) | Pipeline |

---

## Architecture

### Entry Point

`/armchair-architect` — reads `.pipeline/active`, loads state, routes to step or handles subcommand.

Subcommands via `$ARGUMENTS`:

| Command | Action |
|---|---|
| *(default)* | Run or continue from current step |
| `status` | Show current pipeline state |
| `reset` | Confirm and clear active pipeline state |
| `back` | Roll back to previous step |
| `skip interview` | Skip interview (requires `prd.md`) |
| `skip planning` | Skip planning (requires `plan.md`) |
| `list` | List available impl variants |
| `use <component> <impl>` | Switch impl (e.g., `use execute ralph`) |
| `new <feature>` | Create and switch to a new pipeline |
| `switch <feature>` | Switch active pipeline |
| `pipelines` | List all pipelines with current step |

### Two-Level Abstraction

```
/armchair-architect ($ARGUMENTS)
    ↓
SKILL.md orchestrator (reads .pipeline/active → state.json, selects step)
    ↓
┌──────────────────────────────────┐
│  Level 1: WHAT (steps/)          │
│  step contract — stable          │
│  01_init … 07_execute            │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│  Level 2: HOW (impl/)            │
│  swappable implementation        │
│  interview/: ask_user_question   │
│  execute/:   specialized, default,│
│              ralph, tdd, worktree│
│  critique/:  none, default,      │
│              strict              │
└──────────────────────────────────┘
```

### State Schema

`.pipeline/<feature>/state.json` (in user's project, gitignored):

```json
{
  "step": "interview",
  "lang": "ru",
  "interview_mode": "chunked_5",
  "interview_questions_asked": 7,
  "completed": ["init", "setup", "interview_setup"],
  "pending": ["interview", "plan", "impl_plan", "execute"],
  "impl": {
    "interview": "ask_user_question",
    "execute": "specialized",
    "critique": "none",
    "review_every": 0
  }
}
```

### implementation_plan.json Schema

```json
{
  "id": "1.1",
  "category": "backend|frontend|database|infra|test|config",
  "description": "...",
  "context": "...",
  "verification": ["npm test -- --grep 'name'", "curl http://localhost:3000/health"],
  "dependsOn": [],
  "parallel": false,
  "group": "",
  "passes": false,
  "in_progress": false
}
```

- `dependsOn`: ids of tasks that must pass before this task is ready
- `parallel` + `group`: same-group tasks with `parallel: true` run concurrently via Agent tool
- `in_progress`: set at start of implementation; on restart, executor detects interrupted tasks

### Multi-Pipeline

Multiple features can be in different pipeline stages simultaneously:

```
.pipeline/
  active              ← "feature-auth" (name of active pipeline)
  feature-auth/
    state.json
  feature-payments/
    state.json
```

Shell injection reads active pipeline dynamically:
```
!`ACTIVE=$(cat .pipeline/active 2>/dev/null || echo 'default'); cat .pipeline/$ACTIVE/state.json 2>/dev/null || echo '{...}'`
```

Auto-migration: if `.pipeline/state.json` exists without `.pipeline/active`, pipeline automatically
moves it to `.pipeline/default/state.json` on first run.

---

## Closed Design Decisions

| Question | Decision | Reason |
|---|---|---|
| Slash command format | `skills/armchair-architect/SKILL.md` | Plugin-compatible; `${CLAUDE_SKILL_DIR}` resolves step paths |
| Subcommands | `$ARGUMENTS` routing in SKILL.md | No native subcommand support in Claude Code |
| State injection | `!`cat .pipeline/active...`` | Injects live state before Claude sees prompt |
| Active pipeline file | `.pipeline/active` text file | Only mechanism compatible with shell injection at prompt-load time |
| Impl switching | `use <component> <impl>` command | Explicit, auditable, no manual JSON editing |
| Task split | Claude proposes, user approves | Prevents silent scope changes |
| Bilingual sync | Russian primary, English derived at phase boundaries | Eliminates translation drift |
| impl_plan + tasks merged | JSON generated immediately after md approval | Users never approved md without wanting JSON |
| Critique opt-in | `none` is default | Two extra subagent calls add latency; should be explicit choice |
| TDD requires ralph | Default executor unsuitable (context polluted by planning history) | Ralph runs each task in fresh session |
| Parallel results via temp files | Subagents write `task_<id>_result.json`, main executor merges | Avoids concurrent writes to `implementation_plan.json` |
| Ralph invocation | Manual: tell user to run `/ralph-loop` | Claude Code has no skill-to-skill API |
| Specialized executor as default | `specialized` replaces `default` as default executor | Parallel task scope discipline at no cost for sequential tasks; `specialized.md` is a thin extension of `default.md`, not a fork |
| Specialization parallel-only | Role persona added only in Agent dispatch, not sequential tasks | Main LLM has full planning context — adding a role persona risks refusing cross-cutting changes |

---

## Installation

```bash
# Global (available in all projects)
git clone https://github.com/potapyich/armchair-architect ~/.claude/plugins/armchair-architect

# Per-project
git clone https://github.com/potapyich/armchair-architect .claude/plugins/armchair-architect
```

Configure in `settings.json`:
```json
{ "plugins": ["~/.claude/plugins/armchair-architect"] }
```

Update: `git pull` in plugin directory.

---

## Open Questions (Deferred)

- Skill-to-skill invocation — would enable direct ralph integration without manual handoff
- Ralphex executor — waiting for API stabilization
