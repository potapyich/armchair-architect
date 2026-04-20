# Impl: Execute via Ralph Loop (TDD mode)

Same as `ralph.md` — delegates to ralph-loop. Each task in `implementation_plan.json`
is expected to have a `tdd` block injected by the tasks step.

To switch to this executor:
```
/armchair-architect use execute tdd
```

To switch back:
```
/armchair-architect use execute ralph
```

---

## Prerequisites

ralph-loop plugin must be installed. TDD mode runs on top of ralph — it is not a
replacement. The quality advantage of ralph (fresh context per task) is essential
for sustained TDD execution.

---

## How to Invoke

Tell the user:

> Run `/ralph-loop` to start TDD execution.
> ralph will process each task in `implementation_plan.json` in order.
>
> For each task, the TDD protocol is embedded in the task's `tdd` field:
> 1. Write failing tests first (`verify_red` must fail)
> 2. Implement until tests pass (`verify_green` must pass)
> 3. Refactor if needed, re-verify
>
> Suggested: start with 2–3 tasks supervised to confirm the TDD loop is working.

---

## Task Schema (TDD)

Tasks must have been generated with the TDD flag set. Each task should contain:

```json
{
  "id": "1.1",
  "category": "backend",
  "description": "Precise description of what to implement",
  "context": "Any non-obvious background",
  "tdd": {
    "tests_first": "Write failing tests for this task before writing any implementation",
    "verify_red": "<shell command that must fail before implementation>",
    "verify_green": "<shell command that must pass after implementation>"
  },
  "verification": ["<final verification command>"],
  "passes": false
}
```

---

## Resuming After Ralph

When ralph completes, run `/armchair-architect` to sync state and check remaining tasks.

<!--
TDD mode requires ralph because by the execute phase, the main session context is
already occupied with PRD, interview, and planning history. Ralph's fresh-context-per-task
model is what makes test-first discipline reliable.
-->
