# Step 05 — Implementation Plan & Tasks

## Goal

Break each block from `plan.md` into concrete steps, get approval, then immediately
generate `implementation_plan.json`. Plan and tasks are one step — approval of the
markdown means the JSON gets generated right away.

## Instructions

### 1. Read plan.md

Use the Read tool to read `plan.md`.

### 2. Check for context7

Before describing specific API calls, check if context7 is available.
If it is, use it to fetch current documentation for the project's dependencies.

### 3. Generate implementation_plan.md

For each block in `plan.md`, produce a list of concrete steps:

```markdown
# Implementation Plan: <Project Name>

## Block 1: <Name>

### 1.1 <Step Name>
**What:** Precise description of what to build/change
**Acceptance:** How we know this is done (observable outcome)
**Notes:** Any non-obvious constraints or considerations

### 1.2 <Step Name>
...

## Block 2: <Name>
...
```

**Step sizing guidelines:**
- Each step should be completable in one focused session
- Steps should produce a verifiable artifact (file, passing test, working endpoint)
- If a step feels vague, break it down further
- If two steps are always done together, merge them

### 4. Generate implementation plan (language-aware)

**If lang = "ru":**
1. Generate `implementation_plan_ru.md` — Russian version.
2. Present for approval (step 6 uses this as the primary document).
3. After approval, generate `implementation_plan.md` — English canonical from confirmed Russian.

**If lang = "en":**
1. Generate `implementation_plan.md` directly. No Russian version.

### 5. Run implementation plan critique (if enabled)

Read `impl.critique` from state. Load `${CLAUDE_SKILL_DIR}/impl/critique/<critique>.md`
and follow its **Implementation Plan Critique** section.

If critique is `none`: skip silently.

### 6. Present for approval

**If lang = "ru":** show `implementation_plan_ru.md` (with critic findings if any). Ask:
> Ревью плана реализации:
> - Шаги слишком крупные (нужно разбить)?
> - Лишние шаги?
> - Пропущенные шаги?
> - Неправильный порядок внутри блока?
>
> Одобряй или говори что поменять.

**If lang = "en":** show `implementation_plan.md` (with critic findings if any). Ask:
> Review the implementation plan:
> - Any steps too coarse-grained (need splitting)?
> - Any steps that shouldn't be there?
> - Any missing steps?
> - Any wrong order within a block?
>
> Approve to generate tasks, or tell me what to fix.

### 7. Apply corrections and re-confirm if needed

Apply corrections to the language-primary version, regenerate English canonical if needed.
If changes were made, re-run critique before re-presenting. Repeat until explicit approval.

### 8. Generate implementation_plan.json

Convert `implementation_plan.md` to JSON. This is a strict mechanical conversion —
do not interpret, add, or remove content beyond what is in the approved markdown.

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
    "dependsOn": [],
    "parallel": false,
    "group": "",
    "passes": false
  }
]
```

**Verification guidelines:**
- Must be shell commands that exit 0 on success, non-0 on failure
- Prefer running specific tests over `npm test` (faster feedback)
- At minimum one verification command per task

**dependsOn:** list of task ids this task cannot start before. Leave `[]` if none.
Example: `"dependsOn": ["1.1", "1.2"]` — this task waits until 1.1 and 1.2 both pass.

**parallel / group:** if multiple tasks can run simultaneously (no shared file writes,
independent modules), set `parallel: true` and assign the same group name (e.g. `"api-layer"`,
`"ui-components"`). Tasks in the same group with `parallel: true` will be launched concurrently.
Leave `parallel: false` and `group: ""` for sequential tasks.

Identify parallelizable tasks during JSON generation and mark them.
The user reviews these markings at the approval gate.

If TDD mode is active, also add a `tdd` block to each task:
```json
"tdd": {
  "tests_first": "Write failing tests before writing the implementation",
  "verify_red": "<command that must fail before implementation>",
  "verify_green": "<command that must pass after implementation>"
}
```

Write to `implementation_plan.json`.

### 10. Show summary

> Generated `implementation_plan.json` with <N> tasks across <M> categories.
>
> Task breakdown:
> - <category>: <count> tasks
> ...
>
> Run `/armchair-architect` to start execution.

If anything looks wrong: tell the user they can run `/armchair-architect` again to
regenerate tasks after editing `implementation_plan.md`.

### 11. Update state

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
