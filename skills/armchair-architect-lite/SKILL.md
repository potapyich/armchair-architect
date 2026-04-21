---
name: armchair-architect-lite
description: Lightweight feature development guide. Single-session PRD → interview → plan → implementation. No state machine, no external dependencies. Compatible with GitHub Copilot and Cursor.
---

# armchair-architect-lite

A single-session feature development guide. Takes a project idea through PRD, focused
interview, planning, and implementation steps — all in one conversation.

**No state machine. No file loading. No external dependencies.**
Works in Claude Code, GitHub Copilot, Cursor, or any LLM chat.

---

## How to use

Run `/armchair-architect-lite` and follow the phases. Each phase ends with an approval gate —
confirm or ask for corrections before proceeding.

---

## Phase 1 — Project Description

Ask the user:

> Describe your project in free form — what it is, why it exists, how it works,
> constraints, tech stack. No need to be structured, I'll organize it.

Detect the language from their response. Set `lang` to `ru` or `en`.

Wait for the user's response before proceeding.

---

## Phase 2 — PRD

Generate a structured PRD from the user's description.

**Structure:**
```
# PRD: <Project Name>

## Overview
<1-2 sentence summary>

## Problem Statement
<what problem this solves and for whom>

## Goals
<numbered success criteria>

## Non-Goals
<explicit exclusions>

## User Stories
<key use cases>

## Technical Requirements
<stack, integrations, constraints>

## Open Questions
<unresolved items — will be addressed in interview>
```

**If lang = ru:** generate PRD in Russian. Present and ask:
> Всё верно? Поправки перед интервью?

**If lang = en:** generate PRD in English. Present and ask:
> Does this capture your project correctly? Any corrections before the interview?

Apply corrections if requested. Repeat until explicit approval.

---

## Phase 3 — Interview

Generate 5–10 targeted questions to fill gaps in the PRD.

Focus on:
- Ambiguous scope (what's in, what's out)
- Missing technical constraints (auth, data model, integrations)
- Edge cases the user may not have considered
- Non-functional requirements (perf, security, availability)
- Dependencies on existing systems

**Format:** ask all questions at once, numbered. User answers in one reply.

**If lang = ru:**
> Несколько вопросов для уточнения деталей:
>
> 1. ...
> 2. ...
> ...
>
> Отвечай по пунктам или пропускай неактуальные.

**If lang = en:**
> A few questions to sharpen the requirements:
>
> 1. ...
> 2. ...
> ...
>
> Answer by number, skip any that don't apply.

After receiving answers: update the PRD with new information. Show a brief summary of
what changed. No need to show the full PRD again unless the user asks.

---

## Phase 4 — Plan

Generate a high-level plan: 2–6 work blocks, each representing a coherent deliverable.

**Structure:**
```
# Plan: <Project Name>

## Block 1: <Name>
**Goal:** <what this block delivers>
**Scope:**
- <item>
- <item>
**Dependencies:** <what must exist before this block starts>
**Deliverable:** <concrete artifact: endpoint, screen, module, etc.>

## Block 2: <Name>
...
```

**Block sizing guidelines:**
- Each block should be independently deployable or testable
- 3-8 blocks for most projects; fewer for small ones
- Database/infra blocks come before the features that depend on them

**If lang = ru:** generate plan in Russian. Ask:
> Ревью плана:
> - Что-то лишнее?
> - Что-то пропущено?
> - Неверный порядок блоков?
>
> Одобряй или говори что изменить.

**If lang = en:** generate plan in English. Ask:
> Review the plan:
> - Anything unnecessary?
> - Anything missing?
> - Wrong block order?
>
> Approve or tell me what to change.

Apply corrections. Repeat until explicit approval.

---

## Phase 5 — Implementation Plan

For each block, produce concrete steps.

**Structure:**
```
# Implementation Plan: <Project Name>

## Block 1: <Name>

### 1.1 <Step Name>
**What:** Precise description of what to build or change
**Acceptance:** How we know this is done (observable outcome)
**Notes:** Any non-obvious constraints

### 1.2 <Step Name>
...

## Block 2: <Name>
...
```

**Step sizing guidelines:**
- Each step completable in one focused session
- Each step produces a verifiable artifact
- If a step feels vague — break it down
- If two steps are always done together — merge them

**If lang = ru:** generate in Russian. Ask:
> Ревью плана реализации:
> - Шаги слишком крупные?
> - Лишние шаги?
> - Пропущенные шаги?
> - Неправильный порядок внутри блока?
>
> Одобряй или говори что поменять.

**If lang = en:** generate in English. Ask:
> Review the implementation plan:
> - Any steps too coarse-grained?
> - Any steps that shouldn't be there?
> - Any missing steps?
> - Any wrong order within a block?
>
> Approve to start execution, or tell me what to fix.

Apply corrections. Repeat until explicit approval.

---

## Phase 6 — Execute

Work through the implementation plan step by step.

### Starting execution

Show the full step list with status:

```
Implementation plan: <N> steps

[ ] 1.1 <Step Name>
[ ] 1.2 <Step Name>
[ ] 2.1 <Step Name>
...
```

Ask:
> How would you like to proceed?
>
> **A)** Run 3 steps — supervised start
> **B)** Run all steps
> **C)** Pick a number
>
> Reply A, B, or C (+ number for C).

### Per-step loop

For each step:

1. **Announce:** `**Step <id>:** <description>`
2. **Implement:** read relevant files, write the code. Minimal change that satisfies the step.
   - Do not refactor unrelated code
   - Do not add features not in the step description
3. **Verify:** run the acceptance criteria. If it's a testable command — run it.
4. **Report:** one line: `Step <id> done.` then move to next.

### If a step is stuck (2 failed attempts)

Show:
```
Step <id> is stuck.

What I tried:
- <attempt 1>
- <attempt 2>

Last error: <error>

Suggested split:
  <id>a: <subtask>
  <id>b: <subtask>

Options:
A) Approve split — continue with subtasks
B) Skip — mark as known issue, continue
C) Stop — investigate manually
```

Wait for user choice before proceeding.

### Completion

When all steps are done:

> All <N> steps complete.
>
> Run `git log --oneline` to review what was built.

---

## What lite omits vs full armchair-architect

| Feature | lite | full |
|---|---|---|
| State persistence across sessions | — | yes |
| Resume after restart | — | yes |
| Swappable executors (ralph, TDD, worktree) | — | yes |
| Critic subagents | — | yes |
| `back` / `skip` / `reset` commands | — | yes |
| Works without Claude Code | yes | — |
| Works in Copilot / Cursor | yes | — |
| Zero setup | yes | yes |
