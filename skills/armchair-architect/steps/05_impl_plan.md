# Step 05 — Implementation Plan (Tactics)

## Goal

Break each block from `plan.md` into concrete, scoped steps. Generate `implementation_plan.md`
for user approval. This is where "too coarse", "not needed", and "missing a step" are caught.

## Instructions

### 1. Read plan.md

Use the Read tool to read `plan.md`.

### 2. Check for context7

Before describing specific API calls in tasks, check if context7 is available.
If it is, use it to fetch current documentation for the project's dependencies.
This helps ensure task descriptions reference accurate, up-to-date APIs.

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

### 4. If lang = "ru", also generate _implementation_plan_ru.md

### 5. Run implementation plan critique (if enabled)

Read `impl.critique` from state. Load `${CLAUDE_SKILL_DIR}/impl/critique/<critique>.md`
and follow its **Implementation Plan Critique** section.

If critique is `none`: skip this step silently.

### 6. Present for approval

Show `implementation_plan.md` to the user (with critic findings inline if any). Ask:

> Review the implementation plan:
> - Any steps too coarse-grained (need splitting)?
> - Any steps that shouldn't be there?
> - Any missing steps?
> - Any wrong order within a block?
>
> Approve to generate execution tasks, or tell me what to fix.

### 7. Apply corrections and re-confirm if needed

Repeat until explicit approval.

### 7. Update state

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

### 9. Confirm

> Implementation plan approved. Run `/armchair-architect` to generate execution tasks.
