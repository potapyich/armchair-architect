# Step 02 — Setup

## Goal

Configure pipeline tooling and execution modes before the interview begins.
All choices are saved to state and applied automatically throughout the pipeline.

## Instructions

### 1. Check for context7

```bash
cat ~/.claude/settings.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok' if d.get('enabledPlugins',{}).get('context7@claude-plugins-official') else 'missing')" 2>/dev/null || echo "missing"
```

If `missing`, offer:
> **context7** is not installed. It fetches up-to-date library documentation into context —
> helps write correct API calls for current dependency versions.
> Add it to `~/.claude/settings.json`? [y/n]

If yes: add `"context7@claude-plugins-official": true` to `enabledPlugins` and write back.
Then tell the user:
> context7 added. **Please restart this Claude Code session**, then run `/armchair-architect`
> to continue from this step.

Stop here — pipeline resumes from step 03 after restart.

If no, or if already `ok`: continue silently.

### 2. Configure critique mode

Ask:
> **Critique mode** — a subagent will review your documents before you approve them.
>
> - **none** — no critic *(default)*
> - **default** — reviews PRD and implementation plan for gaps and wrong assumptions
> - **strict** — same + security, performance, and operational angle
>
> Choose [none / default / strict] or press Enter for none:

Save choice to state:
```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state set-impl critique <chosen>
```

### 3. Configure TDD mode

First detect whether ralph-loop is installed (TDD requires it):

```bash
RALPH=missing
for p in ~/.claude/plugins/ralph-loop/SKILL.md \
         .claude/plugins/ralph-loop/SKILL.md \
         ~/.claude/skills/ralph-loop/SKILL.md; do
  [ -f "$p" ] && RALPH=installed && break
done
if [ "$RALPH" = "missing" ] && [ -f ~/.claude/settings.json ]; then
  python3 -c "import json,sys; d=json.load(open('$HOME/.claude/settings.json')); sys.exit(0 if d.get('enabledPlugins',{}).get('ralph-loop') else 1)" 2>/dev/null && RALPH=installed
fi
echo "$RALPH"
```

**If `RALPH=missing`:** tell the user, save default executor, skip the question:
> **TDD mode** requires ralph-loop, which is not installed.
> Skipping. To enable later: install ralph-loop, then run
> `/armchair-architect use execute tdd`. Continuing with the default executor.

**If `RALPH=installed`:** ask:
> **TDD mode** — each task follows: write failing tests → implement → verify green.
> Increases execution time, adds test coverage.
>
> Enable TDD? [y/n] *(default: n)*

If yes: save to state:
```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state set-impl execute tdd
```

### 4. Configure code review gate

Ask:
> **Code review gate** — a subagent reviews recent code every N completed tasks.
>
> - **off** — no reviews *(default)*
> - **3** — review every 3 tasks
> - **5** — review every 5 tasks
> - **10** — review every 10 tasks
>
> Choose [off / 3 / 5 / 10] or press Enter for off:

Save choice to state (`0` for off, integer N otherwise):
```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state set-impl review_every <chosen_int>
```

### 5. Show summary and advance

Tell the user:
> Setup complete:
> - context7: active / not installed
> - critique: [chosen]
> - TDD: on / off
> - code review gate: every N tasks / off
>
> Run `/armchair-architect` to configure the interview.

Advance pipeline state:

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state advance
```
