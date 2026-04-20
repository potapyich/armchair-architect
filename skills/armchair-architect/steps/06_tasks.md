# Step 06 — Generate Execution Tasks

## Goal

Convert the approved `implementation_plan.md` into `implementation_plan.json` — the task
file that ralph will execute.

## Instructions

### 1. Read implementation_plan.md

Use the Read tool to read `implementation_plan.md`.

### 2. Generate implementation_plan.json

Rules:
- Each step from `implementation_plan.md` becomes one task object
- Tasks must fit within one context window (if a step is too large, note it for splitting)
- Verification steps must be runnable commands — not descriptions
- `passes` is always `false` initially (ralph marks it true after verification)

Schema:
```json
[
  {
    "id": "1.1",
    "category": "<backend|frontend|database|infra|test|config>",
    "description": "Precise description of what to implement",
    "context": "Any non-obvious background the executor needs",
    "verification": [
      "npm test -- --grep 'unit test name'",
      "curl -s http://localhost:3000/endpoint | jq '.status'"
    ],
    "passes": false
  }
]
```

**Verification guidelines:**
- Must be shell commands that exit 0 on success, non-0 on failure
- Prefer running specific tests over `npm test` (faster feedback)
- For UI tasks: include a check that the file exists and contains expected content
- At minimum one verification per task

### 3. Write the file

Write the generated JSON to `implementation_plan.json`.

### 4. Ask about TDD mode

Before advancing, ask the user:

> Use TDD mode? Each task will follow: write failing tests → implement → verify green. [y/n]
>
> Requires ralph-loop. Adds test coverage but increases execution time per task.

If yes: update `impl.execute` to `tdd` in state.json:
```bash
python3 -c "
import json
with open('.pipeline/state.json') as f: s = json.load(f)
s.setdefault('impl', {})['execute'] = 'tdd'
with open('.pipeline/state.json', 'w') as f: json.dump(s, f, indent=2)
"
```

If no: leave `impl.execute` unchanged.

### 5. Show summary

Display:
> Generated `implementation_plan.json` with <N> tasks across <M> categories.
>
> Task breakdown:
> - <category>: <count> tasks
> ...
>
> Run `/armchair-architect` to start execution.

### 6. Update state

Advance pipeline state:

```bash
python3 -c "
import json
with open('.pipeline/state.json') as f: s = json.load(f)
cur = s['step']
s['completed'] = s.get('completed', []) + [cur]
s['pending'] = [x for x in s.get('pending', []) if x != cur]
s['step'] = s['pending'][0] if s['pending'] else 'done'
with open('.pipeline/state.json', 'w') as f: json.dump(s, f, indent=2)
"
```
