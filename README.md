# armchair-architect

A feature development pipeline for Claude Code. Takes a project from raw idea through
structured PRD, planning, and automated execution.

Two variants:

| | armchair-architect | armchair-architect-lite |
|---|---|---|
| State persistence | yes | — |
| Resume after restart | yes | — |
| Swappable executors | yes | — |
| Critic subagents | yes | — |
| Multi-pipeline support | yes | — |
| Works without Claude Code | — | yes |
| Works in Copilot / Cursor | — | yes |

## armchair-architect — Full Pipeline

```
/armchair-architect → PRD → Interview → plan.md → implementation_plan.md → implementation_plan.json → execute
```

1. **Init** — describe your project, get a structured PRD
2. **Setup** — configure context7, critique mode, TDD mode, code review gate
3. **Interview** — targeted questions to fill gaps, deepen technical detail
4. **Plan** — high-level work blocks, user-approved
5. **Implementation Plan** — concrete steps per block + execution JSON, user-approved
6. **Execute** — run tasks autonomously (default executor or ralph)

## armchair-architect-lite — Single Session

```
/armchair-architect-lite → PRD → Interview → Plan → Implementation Plan → Execute
```

Same phases as the full pipeline, in a single prompt file. No state machine, no external
dependencies. Works in Claude Code, GitHub Copilot, Cursor, or any LLM chat.

Use when:
- You want zero setup — just invoke and go
- You're in Copilot or Cursor and can't install the full plugin
- The project is small enough to complete in one session

## Install

### Global (all projects)

```bash
git clone https://github.com/potapyich/armchair-architect ~/.claude/plugins/armchair-architect
```

Add to `~/.claude/settings.json`:
```json
{
  "plugins": ["~/.claude/plugins/armchair-architect"]
}
```

### Per-project

```bash
git clone https://github.com/potapyich/armchair-architect .claude/plugins/armchair-architect
```

Add to `.claude/settings.json` in your project:
```json
{
  "plugins": [".claude/plugins/armchair-architect"]
}
```

### GitHub Copilot / Cursor (lite only)

Copy `skills/armchair-architect-lite/SKILL.md` into your repo as a custom instruction or
agent instruction file for your editor.

### Update

```bash
cd ~/.claude/plugins/armchair-architect && git pull
```

## Usage

```bash
/armchair-architect              # start or continue from current step
/armchair-architect status       # show current pipeline state
/armchair-architect reset        # clear active pipeline state and start over
/armchair-architect back         # return to previous step
/armchair-architect skip interview   # skip to planning (requires prd.md)
/armchair-architect skip planning    # skip to impl plan (requires plan.md)
/armchair-architect list         # show available impl variants

# Multi-pipeline
/armchair-architect pipelines        # list all pipelines with current step
/armchair-architect new <feature>    # create and switch to a new pipeline
/armchair-architect switch <feature> # switch active pipeline

# Swap executors and modes
/armchair-architect use execute ralph       # switch to ralph executor
/armchair-architect use execute tdd         # switch to TDD executor (requires ralph)
/armchair-architect use execute worktree    # switch to git worktree executor
/armchair-architect use critique default    # enable critic subagents
/armchair-architect use critique strict     # enable strict critic (security/perf angle)

/armchair-architect-lite         # single-session version, no state
```

## Requirements

- [Claude Code](https://claude.ai/code)
- [ralph-loop](https://github.com/anthropics/ralph) *(optional — for ralph/TDD/worktree executors)*

## Files Created in Your Project

| File | When | What |
|---|---|---|
| `prd.md` | Step 1 | Product requirements (English canonical) |
| `prd_ru.md` | Step 1 (if lang=ru) | PRD in Russian — primary for Russian users |
| `plan.md` | Step 4 | Strategy plan (English canonical) |
| `plan_ru.md` | Step 4 (if lang=ru) | Strategy plan in Russian — primary for Russian users |
| `implementation_plan.md` | Step 5 | Detailed steps (English canonical) |
| `implementation_plan_ru.md` | Step 5 (if lang=ru) | Detailed steps in Russian |
| `implementation_plan.json` | Step 5 | Execution tasks (generated after approval) |
| `progress.md` | Step 6 | Execution progress — written on context handoff |
| `escalation.md` | Step 6 | Written when a task reveals a plan-level problem |
| `.pipeline/active` | Throughout | Name of the active pipeline |
| `.pipeline/<feature>/state.json` | Throughout | Pipeline state (gitignored) |

## Design

See [DESIGN.md](./DESIGN.md) for full architecture documentation.
