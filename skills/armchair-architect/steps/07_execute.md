# Step 07 — Execute

## Goal

Run the implementation plan using the configured executor.

## Instructions

### 1. Resolve executor

Read `impl.execute` from state. Default: `default`.

- `default` — built-in executor: I implement tasks here in this session
- `ralph` — delegates to ralph-loop plugin running in a separate session

Load the corresponding impl file: `${CLAUDE_SKILL_DIR}/impl/execute/<impl>.md`

### 2. context7 reminder

If context7 is available, use it when a task involves an external library — check the
current API before writing code. Do not look up documentation for libraries you are
already certain about; only use it when the specific API call matters for correctness.

### 3. Pre-flight check

Verify `implementation_plan.json` exists:

```bash
cat implementation_plan.json | jq 'length'
```

If missing, tell the user:
> `implementation_plan.json` not found. Run `/armchair-architect` from Step 06 to generate it first.

Show current task status:
```bash
cat implementation_plan.json | jq '[.[] | {id, description: .description[:60], passes}]'
```

Tell the user:
> Found <N> tasks, <M> remaining (passes: false).

### 4. Ask how to proceed

> How would you like to run?
>
> **A)** Run 3 tasks — supervised start to verify things work *(recommended)*
> **B)** Run all tasks — go to completion
> **C)** Pick a number
>
> Reply A, B, C (+ number for C).

Wait for user's reply, then follow the impl file instructions with the chosen task count.

### 5. Context handoff reminder

If you notice you're approaching context limits (~40-50%), warn the user:

> Approaching context limit. Before starting a new session:
> 1. `implementation_plan.json` has task status (`passes: true/false`)
> 2. In the new session, run `/armchair-architect` — it will resume from `execute` step
> 3. Execution will continue from the first `passes: false` task.

### 6. On task failure or stuck task

If a task fails after 2 fix attempts, propose a split:

> Task `<id>` appears stuck. Suggested split:
> - `<id>a`: <subtask description>
> - `<id>b`: <subtask description>
> - `<id>c`: <subtask description>
>
> Approve split? The original task will be replaced in `implementation_plan.json`.

Wait for user approval before modifying `implementation_plan.json`.

### 7. Completion

When all tasks have `passes: true`:

> All tasks complete.
>
> Summary:
> - Tasks completed: <N>
> - Verification commands run: <N>
>
> Run `git log --oneline` to review commits, or check `progress.md` for full execution log.

Update state:
```json
{
  "step": "done",
  "completed": ["init", "interview_setup", "interview", "plan", "impl_plan", "tasks", "execute"],
  "pending": []
}
```
