# Step 01 — Init: Input & PRD Generation

## Goal

Gather the user's project description and generate a structured PRD.

## Instructions

### 0. Check for context7

Run:
```bash
cat ~/.claude/settings.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok' if d.get('enabledPlugins',{}).get('context7@claude-plugins-official') else 'missing')" 2>/dev/null || echo "missing"
```

If the result is `missing`, offer to the user:
> **context7** is not installed. It's a plugin that fetches up-to-date library documentation
> directly into context — helps write correct API calls for current dependency versions.
> Add it to `~/.claude/settings.json`? [y/n]

If yes: read `~/.claude/settings.json`, add `"context7@claude-plugins-official": true` to
the `enabledPlugins` object, write it back. Then tell the user:
> context7 added. **Restart this Claude Code session** to activate it, then re-run `/armchair-architect`.

If no: continue without context7.

If the result is `ok`: continue silently (no message needed).

### 1. Check for existing PRD

Try to read `prd.md` using the Read tool (or equivalent file access).

If found, show the user:

> I found an existing PRD (`prd.md`). How would you like to proceed?
>
> **A)** Continue with the existing PRD — skip to next step
> **B)** Start fresh — describe your project from scratch (existing PRD will be overwritten)

Wait for the user's choice (A or B).
- If **A**: confirm it's loaded, update state to `interview_setup`, and stop this step.
- If **B**: proceed with the full init flow below.

### 2. Detect input language

Check what language the user has been writing in this session.
Set `lang` in state accordingly: `"ru"` or `"en"`.

### 3. Request project description

If no project description has been given yet, ask the user:

> Describe your project in free form — dump everything you know: what it is, why it exists,
> how it works, constraints, tech stack. No need to be structured, I'll organize it.

Wait for the user's response before proceeding.

### 4. Check for existing CLAUDE.md

Use the Read tool to check if `CLAUDE.md` exists in the current project.
- If found: read it and note the tech stack and architectural decisions.
- If not found: note this; offer at the end of this step to create one or defer.

### 5. Generate PRD

**If input was in Russian:**
1. Generate `_prd_ru.md` — structured PRD in Russian, based on the user's description.
2. Generate `prd.md` — English translation/adaptation of `_prd_ru.md`.

**If input was in English:**
1. Generate `prd.md` directly.

PRD structure:
```markdown
# Product Requirements Document: <Project Name>

## Overview
<1-2 sentence summary>

## Problem Statement
<what problem this solves and for whom>

## Goals
<numbered list of success criteria>

## Non-Goals
<explicit exclusions>

## User Stories
<key use cases>

## Technical Requirements
<stack, integrations, constraints>

## Open Questions
<unresolved items — will be addressed in interview>
```

### 6. Run PRD critique (if enabled)

Read `impl.critique` from state. Load `${CLAUDE_SKILL_DIR}/impl/critique/<critique>.md`
and follow its **PRD Critique** section.

If critique is `none`: skip this step silently.

If findings are returned: save them to state as `critique_prd` (they feed into interview).

### 7. Present and confirm

Show the generated PRD to the user (and critic findings if any). Ask:
> Does this capture your project correctly? Any corrections before we move to interview setup?

Apply any corrections, then proceed.

### 8. Update state

Advance pipeline state — move current step to completed, set next step from pending:

```bash
python3 -c "
import json
with open('.pipeline/state.json') as f: s = json.load(f)
cur = s['step']
s['completed'] = s.get('completed', []) + [cur]
s['pending'] = [x for x in s.get('pending', []) if x != cur]
s['step'] = s['pending'][0] if s['pending'] else 'done'
s['lang'] = '<detected lang>'
with open('.pipeline/state.json', 'w') as f: json.dump(s, f, indent=2)
"
```

Replace `<detected lang>` with `ru` or `en`.

### 9. Offer CLAUDE.md creation (if missing)

If `CLAUDE.md` was not found:
> No CLAUDE.md found. Want me to create one now with the stack and context from your project
> description? You can edit it later.

If yes: generate a minimal `CLAUDE.md` with tech stack and project context.
