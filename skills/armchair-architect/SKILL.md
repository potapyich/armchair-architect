---
name: armchair-architect
description: Feature development pipeline. Guides a project from idea through PRD, planning, and automated execution. Usage: /armchair-architect [status|reset|back|skip <step>|use <component> <impl>|list|new <feature>|switch <feature>|pipelines]
---

Current pipeline state:
```json
!`ACTIVE=$(cat .pipeline/active 2>/dev/null || echo 'default'); cat .pipeline/$ACTIVE/state.json 2>/dev/null || echo '{"step":"init","completed":[],"pending":["init","setup","interview_setup","interview","plan","impl_plan","execute"],"impl":{"interview":"ask_user_question","execute":"default","critique":"none"}}'`
```

Active pipeline: `!`cat .pipeline/active 2>/dev/null || echo 'default'``

Skill directory: ${CLAUDE_SKILL_DIR}

Arguments: "$ARGUMENTS"

---

## Routing

Read the state above and the arguments, then act accordingly:

### If arguments starts with "new "

Parse: `new <feature>`

```bash
mkdir -p .pipeline/<feature>
echo '<feature>' > .pipeline/active
```

Confirm:
> Created pipeline **<feature>**. Run `/armchair-architect` to start.

Do not proceed further.

### If arguments starts with "switch "

Parse: `switch <feature>`

Check `.pipeline/<feature>/state.json` exists:
```bash
ls .pipeline/<feature>/state.json 2>/dev/null && echo "found" || echo "missing"
```

If missing:
> Pipeline **<feature>** not found. Use `/armchair-architect new <feature>` to create it.

If found: write active file and confirm:
```bash
echo '<feature>' > .pipeline/active
```
> Switched to pipeline **<feature>** (step: <current step from its state>).

Do not proceed further.

### If arguments = "pipelines"

```bash
python3 -c "
import json, os
active = open('.pipeline/active').read().strip() if os.path.exists('.pipeline/active') else 'default'
if not os.path.exists('.pipeline'):
    print('No pipelines found.')
else:
    found = False
    for d in sorted(os.listdir('.pipeline')):
        if d == 'active': continue
        sp = f'.pipeline/{d}/state.json'
        if os.path.exists(sp):
            step = json.load(open(sp)).get('step', '?')
            marker = '*' if d == active else ' '
            print(f'{marker} {d}: {step}')
            found = True
    if not found: print('No pipelines found.')
"
```

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
rm -f .pipeline/$(cat .pipeline/active 2>/dev/null || echo 'default')/state.json
```
Confirm deletion.
If declined: do nothing.

Do not proceed further.

### If arguments = "back"
Return to the previous step without full reset.

```bash
python3 -c "
import json, os, sys
active = open('.pipeline/active').read().strip() if os.path.exists('.pipeline/active') else 'default'
sp = f'.pipeline/{active}/state.json'
with open(sp) as f: s = json.load(f)
if not s.get('completed'):
    print('NOTHING_TO_ROLLBACK'); sys.exit(0)
prev = s['completed'].pop()
s['pending'] = [prev] + s.get('pending', [])
s['step'] = prev
with open(sp, 'w') as f: json.dump(s, f, indent=2)
print(f'ROLLED_BACK_TO:{prev}')
"
```

If output is `NOTHING_TO_ROLLBACK`:
> Nothing to roll back — pipeline hasn't started yet.

Otherwise confirm (replace `<step>` with the value after `ROLLED_BACK_TO:`):
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
python3 -c "
import json, os
active = open('.pipeline/active').read().strip() if os.path.exists('.pipeline/active') else 'default'
sp = f'.pipeline/{active}/state.json'
with open(sp) as f: s = json.load(f)
skip = ['interview_setup', 'interview']
for st in skip:
    if st in s.get('pending', []):
        s['pending'].remove(st)
    if st not in s.get('completed', []):
        s.setdefault('completed', []).append(st)
s['step'] = s['pending'][0] if s['pending'] else 'done'
with open(sp, 'w') as f: json.dump(s, f, indent=2)
print(s['step'])
"
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
python3 -c "
import json, os
active = open('.pipeline/active').read().strip() if os.path.exists('.pipeline/active') else 'default'
sp = f'.pipeline/{active}/state.json'
with open(sp) as f: s = json.load(f)
if 'plan' in s.get('pending', []): s['pending'].remove('plan')
if 'plan' not in s.get('completed', []): s.setdefault('completed', []).append('plan')
s['step'] = s['pending'][0] if s['pending'] else 'done'
with open(sp, 'w') as f: json.dump(s, f, indent=2)
print(s['step'])
"
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
Parse: `use <component> <impl>` (e.g., `use execute ralphex`)

```bash
python3 -c "
import json, os
active = open('.pipeline/active').read().strip() if os.path.exists('.pipeline/active') else 'default'
sp = f'.pipeline/{active}/state.json'
with open(sp) as f: s = json.load(f)
s.setdefault('impl', {})['<component>'] = '<impl>'
with open(sp, 'w') as f: json.dump(s, f, indent=2)
"
```

Confirm: "Switched <component> to <impl>."

Do not proceed further.

### If arguments = "" or "run" (default — run or continue)

First, auto-migrate legacy state if needed:

```bash
python3 -c "
import os, shutil
if os.path.exists('.pipeline/state.json') and not os.path.exists('.pipeline/active'):
    os.makedirs('.pipeline/default', exist_ok=True)
    shutil.move('.pipeline/state.json', '.pipeline/default/state.json')
    open('.pipeline/active', 'w').write('default')
    print('Migrated existing pipeline to .pipeline/default/')
"
```

Then validate state:

```bash
python3 -c "
import json, sys, os
VALID_STEPS = ['init','setup','interview_setup','interview','plan','impl_plan','execute','done']
VALID_EXECUTE = ['default','ralph','tdd','worktree']
VALID_CRITIQUE = ['none','default','strict']
VALID_LANG = ['ru','en']
active = open('.pipeline/active').read().strip() if os.path.exists('.pipeline/active') else 'default'
state_path = f'.pipeline/{active}/state.json'
try:
    with open(state_path) as f: s = json.load(f)
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
> Fix `.pipeline/<active>/state.json` manually, or run `/armchair-architect reset` to start over.

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

After completing a step, update the active pipeline state:
- Move the completed step from `pending` to `completed`
- Set `step` to the next pending step

If `.pipeline/<active>/` directory does not exist, create it first:
```bash
ACTIVE=$(cat .pipeline/active 2>/dev/null || echo 'default')
mkdir -p .pipeline/$ACTIVE
```
