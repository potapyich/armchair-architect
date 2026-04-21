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
python3 -c "
import json
import os as _os; _active = open('.pipeline/active').read().strip() if _os.path.exists('.pipeline/active') else 'default'; _sp = f'.pipeline/{_active}/state.json'
with open(_sp) as f: s = json.load(f)
s.setdefault('impl', {})['critique'] = '<chosen>'
with open(_sp, 'w') as f: json.dump(s, f, indent=2)
"
```

### 3. Configure TDD mode

Ask:
> **TDD mode** — each task follows: write failing tests → implement → verify green.
> Requires ralph-loop. Increases execution time, adds test coverage.
>
> Enable TDD? [y/n] *(default: n)*

If yes: save to state:
```bash
python3 -c "
import json
import os as _os; _active = open('.pipeline/active').read().strip() if _os.path.exists('.pipeline/active') else 'default'; _sp = f'.pipeline/{_active}/state.json'
with open(_sp) as f: s = json.load(f)
s.setdefault('impl', {})['execute'] = 'tdd'
with open(_sp, 'w') as f: json.dump(s, f, indent=2)
"
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
python3 -c "
import json
import os as _os; _active = open('.pipeline/active').read().strip() if _os.path.exists('.pipeline/active') else 'default'; _sp = f'.pipeline/{_active}/state.json'
with open(_sp) as f: s = json.load(f)
s.setdefault('impl', {})['review_every'] = <chosen_int>
with open(_sp, 'w') as f: json.dump(s, f, indent=2)
"
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
python3 -c "
import json
import os as _os; _active = open('.pipeline/active').read().strip() if _os.path.exists('.pipeline/active') else 'default'; _sp = f'.pipeline/{_active}/state.json'
with open(_sp) as f: s = json.load(f)
cur = s['step']
s['completed'] = s.get('completed', []) + [cur]
s['pending'] = [x for x in s.get('pending', []) if x != cur]
s['step'] = s['pending'][0] if s['pending'] else 'done'
with open(_sp, 'w') as f: json.dump(s, f, indent=2)
"
```
