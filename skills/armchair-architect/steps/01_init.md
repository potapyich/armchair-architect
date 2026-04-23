# Step 01 — Init: Input & PRD Generation

## Goal

Gather the user's project description and generate a structured PRD.

## Instructions

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

**If input was in Russian:**
1. Generate `prd_ru.md` — structured PRD in Russian, based on the user's description.
2. Present `prd_ru.md` to the user for review and corrections (step 6).
3. After confirmation, generate `prd.md` — English canonical derived from the confirmed `prd_ru.md`.

**If input was in English:**
1. Generate `prd.md` directly. No Russian version.

### 6. Run PRD critique (if enabled)

Read `impl.critique` from state. Load `${CLAUDE_SKILL_DIR}/impl/critique/<critique>.md`
and follow its **PRD Critique** section.

If critique is `none`: skip silently.

If findings are returned: save them to state as `critique_prd` (they feed into interview).

### 7. Present and confirm

**If lang = "ru":** show `prd_ru.md` to the user (and critic findings if any). Ask:
> Всё верно? Поправки перед тем как перейдём к настройке интервью?

Apply corrections to `prd_ru.md`, then regenerate `prd.md` from the confirmed Russian.

**If lang = "en":** show `prd.md` (and critic findings if any). Ask:
> Does this capture your project correctly? Any corrections before we move to interview setup?

Apply any corrections, then proceed.

### 8. Update state

Save the detected language, then advance pipeline state:

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state set-lang <detected lang>
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -m state advance
```

Replace `<detected lang>` with `ru` or `en`.

### 9. Offer CLAUDE.md creation (if missing)

If `CLAUDE.md` was not found:
> No CLAUDE.md found. Want me to create one now with the stack and context from your project
> description? You can edit it later.

If yes: generate a minimal `CLAUDE.md` with tech stack and project context.
