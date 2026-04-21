# Impl: Embedded Executor (default)

## Overview

Autonomous task executor built into the pipeline. No external dependencies.
Reads `implementation_plan.json`, implements tasks one by one, verifies each, marks done.

---

## Response discipline

Keep output short during execution — long responses get cut off mid-task:
- Announce task in one line, then act immediately
- Do not explain what you are about to do — just do it
- Do not narrate file reads or edits — make the change, move on
- After verification passes: one line confirmation, next task

---

## Execution Loop

Before starting: note the task count N chosen by the user in step 07 (e.g. 3, 10, or "all").
Track how many tasks you complete in this run. Stop after N tasks even if more remain.

### 1. Load the task list and find ready tasks

```bash
cat implementation_plan.json
```

Build the set of completed task ids (`passes: true`).

A task is **ready** if:
- `passes: false`
- all ids in its `dependsOn` array have `passes: true` (or `dependsOn` is empty/missing)

If all tasks have `passes: true` — execution is complete, go to Completion.

If no ready tasks remain but some have `passes: false` — dependency deadlock. Tell the user:
> Dependency deadlock: remaining tasks cannot start because their dependencies have not passed.
> Check `implementation_plan.json` for failed prerequisite tasks or dependency cycles.

Stop.

### 2. Dispatch: parallel or sequential

From the ready tasks, check for parallel groups.

**Sequential (default):** if no ready tasks have `parallel: true`, pick the first ready task
and proceed to step 3 (Announce).

**Parallel group:** if 2 or more ready tasks share the same `group` value and all have
`parallel: true`:

1. Collect all ready tasks in that group.
2. For each task, launch a subagent in parallel:

   ```
   Agent(prompt="You are implementing a single task from a feature development plan.

   Task id: <id>
   Description: <description>
   Context: <context>
   Category: <category>

   Implement this task. Then run each verification command:
   <verification commands>

   Write your result to file task_<id>_result.json:
   {\"id\": \"<id>\", \"passes\": true, \"error\": \"\"}
   or on failure:
   {\"id\": \"<id>\", \"passes\": false, \"error\": \"<last error output>\"}

   Rules:
   - Make the smallest change that satisfies the task description
   - Do not modify files outside the scope of this task
   - Do not write passes: true unless ALL verification commands exit 0")
   ```

3. Wait for all subagents to complete.

4. Merge results into `implementation_plan.json` and clean up temp files:

   ```bash
   python3 -c "
   import json, glob, os
   with open('implementation_plan.json') as f: tasks = json.load(f)
   id_map = {t['id']: t for t in tasks}
   for rf in sorted(glob.glob('task_*_result.json')):
       with open(rf) as f: r = json.load(f)
       if r['id'] in id_map:
           id_map[r['id']]['passes'] = r['passes']
       os.remove(rf)
   with open('implementation_plan.json', 'w') as f: json.dump(list(id_map.values()), f, indent=2)
   "
   ```

5. Report:
   > Parallel group **<group>**: <N> tasks passed, <M> failed.
   > Failed: <ids>  ← only if any

6. If any failed → treat each as stuck (go to Stuck Task handling for each failed id).

7. Increment `completed_count` by number of passed tasks. Go back to step 1.

### 3. Announce the task

Tell the user:
> **Task <id>:** <description>

### 4. Implement the task

Read relevant files, understand the context, write the code.

Guidelines:
- Make the smallest change that satisfies the task description
- Do not refactor unrelated code
- Do not add features not in the task description
- If the task depends on a previous task's output, verify that output exists first

### 5. Run verification

For each command in the task's `verification` array, run it with the Bash tool.

A task passes when **all** verification commands exit with code 0.

If a command fails:
- Read the error output carefully
- Attempt a fix
- Re-run the failed command
- Allow up to **2 fix attempts** before declaring the task stuck

### 6. Mark task result

**On pass:** Update `implementation_plan.json` — set `"passes": true` for this task id.

```bash
# Read current json, update the task, write back
cat implementation_plan.json | jq '
  map(if .id == "<task_id>" then .passes = true else . end)
' > /tmp/plan_update.json && mv /tmp/plan_update.json implementation_plan.json
```

Announce:
> Task <id> passed verification.

**On stuck (2 failed fix attempts):** Do NOT mark as passed. Go to Stuck Task handling below.

### 7. Code review gate (if configured)

After marking a task passed, check if a review is due:

```bash
cat .pipeline/state.json | python3 -c "import json,sys; s=json.load(sys.stdin); print(s.get('impl',{}).get('review_every',0))"
```

If `review_every` is 0 or missing — skip. Otherwise, if `completed_count % review_every == 0`:

Run:
```bash
git diff HEAD~<review_every> --stat
git diff HEAD~<review_every>
```

Launch a subagent:
```
Agent(prompt="You are a senior engineer doing a code review.

Recent changes (last <N> tasks):
<git diff output>

Tasks that produced these changes:
<relevant task descriptions from implementation_plan.json>

Review for: correctness, code quality, consistency with the plan,
missing error handling, obvious bugs.
Output: numbered list of issues with severity [high/medium/low]. No praise.
If no issues: say 'No issues found.'")
```

Show findings to the user:
> Code review after task <id> (<N> tasks completed):
> [findings]
>
> Continue? [y / fix first]

- If "y" or no issues: continue immediately.
- If "fix first": pause, wait for user to address issues, then resume.

### 8. Loop

Increment completed task count. If count >= N (the user's chosen limit): go to Mid-run Stop.
Otherwise go back to step 1 — pick the next ready task.

---

## Mid-run Stop

When the task limit is reached (but tasks remain):

```bash
cat implementation_plan.json | jq '[.[] | select(.passes == false)] | length'
```

Tell the user:
> Completed <N> tasks this run. <M> tasks remaining.
>
> State is saved. Run `/armchair-architect` to continue from where we stopped.

---

## Stuck Task Handling

When a task fails after 2 fix attempts:

1. Show the user:
```
Task <id> is stuck.

What I tried:
- <attempt 1 summary>
- <attempt 2 summary>

Last error:
<error output>

Suggested split:
  <id>a: <subtask>
  <id>b: <subtask>
  <id>c: <subtask>  (if applicable)

Options:
A) Approve split — I'll update implementation_plan.json and continue
B) Skip this task — mark as known issue, continue with next
C) Stop — investigate manually, then run /armchair-architect to resume
```

2. Wait for user choice. Do NOT modify `implementation_plan.json` until approved.

3. On split approval:
   - Replace the stuck task entry with the subtask entries (all `passes: false`)
   - Write updated `implementation_plan.json`
   - Resume from the first subtask

---

## Context Budget Awareness

After each completed task, check approximately how much context has been used.
At ~40-50% estimated usage:

1. Write `progress.md`:

```bash
python3 -c "
import json
with open('implementation_plan.json') as f: tasks = json.load(f)
done = [t for t in tasks if t.get('passes')]
remaining = [t for t in tasks if not t.get('passes')]
lines = ['# Execution Progress', '']
lines.append('## Completed')
for t in done:
    lines.append(f'- [{t[\"id\"]}] {t[\"description\"]}')
lines.append('')
lines.append('## Remaining')
for t in remaining:
    lines.append(f'- [{t[\"id\"]}] {t[\"description\"]}')
open('progress.md', 'w').write('\n'.join(lines))
"
```

2. Warn the user:

> Approaching context limit after task <id>.
> Wrote `progress.md` with execution state.
>
> Start a new session and run `/armchair-architect` — it will resume from task <next_id>.

---

## Completion

When all tasks have `"passes": true`:

```bash
cat implementation_plan.json | jq '[.[] | select(.passes == true)] | length'
```

Announce:
> All <N> tasks complete.
>
> Run `git log --oneline -10` to review what was built.

Update pipeline state — set `step` to `"done"`.

---

## Switching to Ralph

If you prefer to use the ralph-loop plugin instead of this executor:

```
/armchair-architect use execute ralph
```

Then see `impl/execute/ralph.md` for how to invoke it.

<!--
## Detection approach (Option C — not implemented, kept for reference)

To auto-detect ralph and use it when available:

  # Check if ralph skill files are present at known locations
  RALPH_GLOBAL=~/.claude/skills/ralph-loop/SKILL.md
  RALPH_LOCAL=.claude/skills/ralph-loop/SKILL.md

  if [ -f "$RALPH_GLOBAL" ] || [ -f "$RALPH_LOCAL" ]; then
    echo "ralph"
  else
    echo "default"
  fi

If detected: delegate to impl/execute/ralph.md
If not: proceed with this embedded executor

Downside: ralph-loop may live in a non-standard path depending on install method.
Upside: zero-config for users who already have ralph.
-->
