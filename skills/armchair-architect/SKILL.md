---
name: armchair-architect
description: Feature development pipeline. Guides a project from idea through PRD, planning, and automated execution. Usage: /armchair-architect [status|reset|back|skip <step>|use <component> <impl>|list|new <feature>|switch <feature>|pipelines|stats]
---

Current pipeline state:
```json
!`ACTIVE=$(cat .pipeline/active 2>/dev/null || echo 'default'); cat .pipeline/$ACTIVE/state.json 2>/dev/null || echo '{"step":"init","completed":[],"pending":["init","setup","interview_setup","interview","plan","impl_plan","execute"],"impl":{"interview":"ask_user_question","execute":"default","critique":"none"}}'`
```

Active pipeline: `!`cat .pipeline/active 2>/dev/null || echo 'default'``

Skill directory: ${CLAUDE_SKILL_DIR}

Arguments: "$ARGUMENTS"

---

All state mutations go through the helper library at `${CLAUDE_SKILL_DIR}/lib/state.py`.
Invoke it with `PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state <command> [args]`.
Available commands: `validate`, `advance`, `rollback-one`, `rollback-to <step>`,
`skip-to-after <step>...`, `set-impl <component> <value>`, `set-lang <ru|en>`,
`auto-migrate`, `list-pipelines`, `create-pipeline <name>`, `switch-pipeline <name>`,
`reset-active`, `emit-event <name> [k=v ...]`, `step-file <step>`, `active-pipeline`, `load`.

---

## Routing

Read the state above and the arguments, then act accordingly:

### If arguments starts with "new "

Parse: `new <feature>`

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state create-pipeline <feature>
```

Confirm:
> Created pipeline **<feature>**. Run `/armchair-architect` to start.

Do not proceed further.

### If arguments starts with "switch "

Parse: `switch <feature>`

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state switch-pipeline <feature>
```

If output is `missing`:
> Pipeline **<feature>** not found. Use `/armchair-architect new <feature>` to create it.

If output is `ok`:
> Switched to pipeline **<feature>** (step: <current step from its state>).

Do not proceed further.

### If arguments = "pipelines"

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state list-pipelines
```

If empty output: "No pipelines found."

Do not proceed further.

### If arguments = "status"
Display the current pipeline state in a readable format:
- Active pipeline name
- Current step
- Completed steps
- Pending steps
- Active impl configuration
- Language setting

Do not proceed further.

### If arguments = "reset"
Ask the user to confirm: "Reset pipeline **<active>** state? All progress will be lost. [y/n]"
If confirmed:
```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state reset-active
```
Confirm deletion.
If declined: do nothing.

Do not proceed further.

### If arguments = "back"
Return to the previous step without full reset.

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state rollback-one
```

If output is `NOTHING_TO_ROLLBACK`:
> Nothing to roll back — pipeline hasn't started yet.

Otherwise emit a `step_back` event and confirm (replace `<step>` with the printed value):
```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state emit-event step_back to=<step>
```
> Rolled back to **<step>**. Run `/armchair-architect` to re-run this step.

Do not proceed further.

### If arguments starts with "skip "

Parse: `skip <name>` where name is one of: `interview`, `planning`.

**`skip interview`**
Check that `prd.md` exists:
```bash
ls prd.md 2>/dev/null && echo "found" || echo "missing"
```
If missing:
> Cannot skip interview — `prd.md` not found. Run `/armchair-architect` to generate it first.
> Stop.

If found:
```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state skip-to-after interview_setup interview
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state emit-event step_skip steps=interview_setup,interview
```
Confirm (replace `<next step>` with printed value):
> Skipped interview. Pipeline continues from **<next step>**.

**`skip planning`**
Check that `plan.md` exists:
```bash
ls plan.md 2>/dev/null && echo "found" || echo "missing"
```
If missing:
> Cannot skip planning — `plan.md` not found. Run `/armchair-architect` to generate it first.
> Stop.

If found:
```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state skip-to-after plan
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state emit-event step_skip steps=plan
```
Confirm (replace `<next step>` with printed value):
> Skipped planning. Pipeline continues from **<next step>**.

Do not proceed further.

### If arguments = "list"

Use the Bash tool to list available implementations for each component:

```bash
echo "=== execute ===" && ls ${CLAUDE_SKILL_DIR}/impl/execute/ | sed 's/\.md//'
echo "=== interview ===" && ls ${CLAUDE_SKILL_DIR}/impl/interview/ | sed 's/\.md//'
echo "=== critique ===" && ls ${CLAUDE_SKILL_DIR}/impl/critique/ | sed 's/\.md//'
```

Then show the current active impl from state:
```
Active: execute=<value>, interview=<value>, critique=<value>
```

Do not proceed further.

### If arguments starts with "use "
Parse: `use <component> <impl>` (e.g., `use execute ralph`)

If `<component>` is `execute` and `<impl>` is one of `tdd`, `worktree`, `ralph` — gate
on ralph-loop being installed:

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

If output is `missing`, refuse and do not modify state:
> Cannot switch to **<impl>** — ralph-loop is not installed.
> Install: `git clone https://github.com/anthropics/ralph ~/.claude/plugins/ralph-loop`
> Then re-run `/armchair-architect use execute <impl>`.

Otherwise (or for any other `<component>`/`<impl>` pair), update state and emit event:

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state set-impl <component> <impl>
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state emit-event impl_change component=<component> to=<impl>
```

Confirm: "Switched <component> to <impl>."

Do not proceed further.

### If arguments = "stats"

Aggregate events from `.pipeline/<active>/events.jsonl`:

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -c "
import collections, state
events = state.read_events()
if not events:
    print('No events recorded yet.')
    raise SystemExit
counts = collections.Counter(e['event'] for e in events)
print('Event counts:')
for ev, n in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'  {ev}: {n}')
passes = [e for e in events if e['event'] == 'task_pass']
stuck = [e for e in events if e['event'] == 'task_stuck']
total_done = len(passes) + len(stuck)
if total_done:
    first_attempt = sum(1 for e in passes if int(e.get('attempts', 1)) == 1)
    print(f'Tasks completed: {total_done} (passed={len(passes)}, stuck={len(stuck)})')
    print(f'First-attempt pass rate: {100 * first_attempt // total_done}%')
by_cat = collections.Counter(e.get('category', '?') for e in stuck)
if by_cat:
    print('Stuck by category:')
    for cat, n in by_cat.most_common():
        print(f'  {cat}: {n}')
"
```

Do not proceed further.

### If arguments = "" or "run" (default — run or continue)

First, auto-migrate legacy state if needed:

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state auto-migrate
```

Then validate state:

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state validate
```

If the output starts with `STATE ERROR:`, stop and tell the user:

> Pipeline state appears corrupted:
> `<error details>`
>
> Fix `.pipeline/<active>/state.json` manually, or run `/armchair-architect reset` to start over.

Otherwise continue.

Resolve the step file from `${CLAUDE_SKILL_DIR}/lib/steps.json` (single source of truth
for the step sequence — never hardcode step names or filenames here):

```bash
STEP=$(PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state load | python3 -c "import json,sys; print(json.load(sys.stdin).get('step',''))")
FILE=$(PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state step-file "$STEP")
echo "${CLAUDE_SKILL_DIR}/steps/$FILE"
```

Read the resolved step file using the Read tool, then follow its instructions exactly.

After completing a step, the step file itself calls `python3 -m state advance` to move
the completed step from `pending` to `completed` and set `step` to the next pending one.
