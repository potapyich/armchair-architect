# doit-cc-plugin

A feature development pipeline for Claude Code. Takes a project from raw idea through
structured PRD, planning, and automated execution.

## Pipeline Overview

```
/armchair-architect → PRD → Interview → plan.md → implementation_plan.md → implementation_plan.json → ralph
```

1. **Init** — describe your project, get a structured PRD
2. **Interview** — targeted questions to fill gaps, deepen technical detail
3. **Plan** — high-level work blocks, user-approved
4. **Implementation Plan** — concrete steps per block, user-approved
5. **Tasks** — execution-ready JSON with verification commands
6. **Execute** — ralph runs the tasks autonomously

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

### Update

```bash
cd ~/.claude/plugins/doit-cc-plugin && git pull
```

## Usage

```bash
/armchair-architect              # start or continue from current step
/armchair-architect status       # show current state
/armchair-architect reset        # clear state and start over
/armchair-architect use execute ralphex   # switch executor
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
