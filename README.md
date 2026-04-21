# doit-cc-plugin

A feature development pipeline for Claude Code. Takes a project from raw idea through
structured PRD, planning, and automated execution.

Two variants:

| | armchair-architect | armchair-architect-lite |
|---|---|---|
| State persistence | yes | — |
| Resume after restart | yes | — |
| Swappable executors | yes | — |
| Critic subagents | yes | — |
| Works without Claude Code | — | yes |
| Works in Copilot / Cursor | — | yes |

## armchair-architect — Full Pipeline

```
/armchair-architect → PRD → Interview → plan.md → implementation_plan.md → implementation_plan.json → execute
```

1. **Init** — describe your project, get a structured PRD
2. **Setup** — configure context7, critique mode, TDD mode
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
git clone https://github.com/potapyich/doit-cc-plugin ~/.claude/plugins/doit-cc-plugin
```

Add to `~/.claude/settings.json`:
```json
{
  "plugins": ["~/.claude/plugins/doit-cc-plugin"]
}
```

### Per-project

```bash
git clone https://github.com/potapyich/doit-cc-plugin .claude/plugins/doit-cc-plugin
```

Add to `.claude/settings.json` in your project:
```json
{
  "plugins": [".claude/plugins/doit-cc-plugin"]
}
```

### GitHub Copilot / Cursor (lite only)

Copy `skills/armchair-architect-lite/SKILL.md` into your repo as a custom instruction or
agent instruction file for your editor.

### Update

```bash
cd ~/.claude/plugins/doit-cc-plugin && git pull
```

## Usage

```bash
/armchair-architect              # start or continue from current step
/armchair-architect status       # show current state
/armchair-architect reset        # clear state and start over
/armchair-architect back         # return to previous step
/armchair-architect skip interview   # skip to planning (requires prd.md)
/armchair-architect skip planning    # skip to impl plan (requires plan.md)
/armchair-architect list         # show available impl variants
/armchair-architect use execute ralph    # switch to ralph executor
/armchair-architect use execute tdd     # switch to TDD executor
/armchair-architect use execute worktree  # switch to git worktree executor
/armchair-architect use critique default  # enable critic subagents
/armchair-architect use critique strict   # enable strict critic (security/perf angle)

/armchair-architect-lite         # single-session version, no state
```

## Requirements

- [Claude Code](https://claude.ai/code)
- [ralph](https://github.com/anthropics/ralph) for execution phase

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
| `progress.md` | Step 6 | Execution log (written by ralph) |
| `.pipeline/state.json` | Throughout | Pipeline state (gitignored) |

## Design

See [DESIGN.md](./DESIGN.md) for full architecture documentation.
