# Step 04 — Strategy Plan

## Goal

Generate a high-level `plan.md` that the user approves before detailed planning begins.
This is where wrong sequencing and missing modules are caught.

## Instructions

### 1. Read PRD

Use the Read tool to read `prd.md`. Use it as the basis for the plan.

### 2. Generate plan.md

Structure:

```markdown
# Plan: <Project Name>

## Architecture Overview
<Brief description of the main components and how they interact>

## Work Blocks

### Block 1: <Name>
**What:** <What this block delivers>
**Why first:** <Dependency rationale>
**Includes:** <High-level list of work>
**Dependencies:** none / Block N

### Block 2: <Name>
...

## Sequence Rationale
<Why this order — what enables what>

## Risks & Assumptions
<Things that could affect the plan>
```

### 3. If lang = "ru", also generate _plan_ru.md

Mirror structure, content in Russian.

### 4. Present for approval

Show `plan.md` to the user. Ask:

> Does this plan look right?
> - Correct order of work?
> - Any missing blocks?
> - Any blocks that should be removed or merged?
>
> Approve to proceed to detailed planning, or tell me what to change.

### 5. Apply corrections and re-confirm if needed

If the user requests changes, apply them and show the updated plan.
Repeat until the user explicitly approves.

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

### 7. Confirm

> Plan approved. Run `/armchair-architect` to generate the detailed implementation plan.
