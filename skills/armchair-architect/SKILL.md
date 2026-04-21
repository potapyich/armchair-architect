---
name: armchair-architect
description: Feature development pipeline. Guides a project from idea through PRD, planning, and automated execution. Usage: /armchair-architect [status|reset|back|skip <step>|use <component> <impl>|list]
---

Current pipeline state:
```json
!`cat .pipeline/state.json 2>/dev/null || echo '{"step":"init","completed":[],"pending":["init","setup","interview_setup","interview","plan","impl_plan","execute"],"impl":{"interview":"ask_user_question","execute":"default","critique":"none"}}'`
```

Skill directory: ${CLAUDE_SKILL_DIR}

Arguments: "$ARGUMENTS"

---

## Routing

Read the state above and the arguments, then act accordingly:

### If arguments = "status"
Display the current pipeline state in a readable format:
- Current step
- Completed steps
- Pending steps
- Active impl configuration
- Language setting

Do not proceed further.

### If arguments = "reset"
Ask the user to confirm: "Reset pipeline state? All progress will be lost. [y/n]"
If confirmed: use the Bash tool to run `rm -f .pipeline/state.json` and confirm deletion.
If declined: do nothing.

Do not proceed further.

### If arguments = "back"
Return to the previous step without full reset.

Read current state. Take the last item from `completed`. Move it back to the front of `pending`.
Set `step` to that value. Write updated state to `.pipeline/state.json`.

Confirm:
> Rolled back to **<step>**. Run `/armchair-architect` to re-run this step.

If `completed` is empty, tell the user:
> Nothing to roll back — pipeline hasn't started yet.

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

If found: remove `interview_setup` and `interview` from `pending`, add them to `completed`
(if not already there). Set `step` to the next remaining item in `pending`.
Write updated state. Confirm:
> Skipped interview. Pipeline continues from **<next step>**.

**`skip planning`**
Check that `plan.md` exists:
```bash
ls plan.md 2>/dev/null && echo "found" || echo "missing"
```
If missing:
> Cannot skip planning — `plan.md` not found. Run `/armchair-architect` to generate it first.
> Stop.

If found: remove `plan` from `pending`, add to `completed`. Set `step` to next pending item.
Write updated state. Confirm:
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
Parse: `use <component> <impl>` (e.g., `use execute ralphex`)
Read current state, update `impl.<component>` to `<impl>`, write back to `.pipeline/state.json`.
Confirm: "Switched <component> to <impl>."

Do not proceed further.

### If arguments = "" or "run" (default — run or continue)

First, validate state:

```bash
python3 -c "
import json, sys
VALID_STEPS = ['init','setup','interview_setup','interview','plan','impl_plan','execute','done']
VALID_EXECUTE = ['default','ralph','tdd','worktree']
VALID_CRITIQUE = ['none','default','strict']
VALID_LANG = ['ru','en']
try:
    with open('.pipeline/state.json') as f: s = json.load(f)
except FileNotFoundError:
    sys.exit(0)
except Exception as e:
    print(f'STATE ERROR: cannot parse state.json: {e}'); sys.exit(1)
errors = []
step = s.get('step')
if step not in VALID_STEPS:
    errors.append(f'unknown step: {step!r}')
pending = s.get('pending', [])
completed = s.get('completed', [])
if not isinstance(pending, list): errors.append('pending is not a list')
if not isinstance(completed, list): errors.append('completed is not a list')
if isinstance(pending, list) and isinstance(completed, list):
    overlap = set(pending) & set(completed)
    if overlap: errors.append(f'steps in both pending and completed: {sorted(overlap)}')
    if step != 'done' and step not in pending:
        errors.append(f'step {step!r} not in pending')
lang = s.get('lang')
if lang and lang not in VALID_LANG:
    errors.append(f'unknown lang: {lang!r}')
impl = s.get('impl', {})
exe = impl.get('execute')
if exe and exe not in VALID_EXECUTE:
    errors.append(f'unknown impl.execute: {exe!r}')
crit = impl.get('critique')
if crit and crit not in VALID_CRITIQUE:
    errors.append(f'unknown impl.critique: {crit!r}')
if errors:
    print('STATE ERROR: ' + '; '.join(errors)); sys.exit(1)
" 2>&1
```

If the output contains `STATE ERROR:`, stop and tell the user:

> Pipeline state appears corrupted:
> `<error details>`
>
> Fix `.pipeline/state.json` manually, or run `/armchair-architect reset` to start over.

Otherwise continue.

Determine the current step from state. Load and execute the corresponding step file:

| Step | File |
|---|---|
| init | `${CLAUDE_SKILL_DIR}/steps/01_init.md` |
| setup | `${CLAUDE_SKILL_DIR}/steps/02_setup.md` |
| interview_setup | `${CLAUDE_SKILL_DIR}/steps/03_interview_setup.md` |
| interview | `${CLAUDE_SKILL_DIR}/steps/04_interview.md` |
| plan | `${CLAUDE_SKILL_DIR}/steps/05_plan.md` |
| impl_plan | `${CLAUDE_SKILL_DIR}/steps/06_impl_plan.md` |
| execute | `${CLAUDE_SKILL_DIR}/steps/07_execute.md` |

Read the step file using the Read tool, then follow its instructions exactly.

After completing a step, update `.pipeline/state.json`:
- Move the completed step from `pending` to `completed`
- Set `step` to the next pending step

Use the Bash tool to write state updates:
```bash
# Example — always read current state first, then write merged result
cat .pipeline/state.json
```

If `.pipeline/` directory does not exist, create it first:
```bash
mkdir -p .pipeline
```
