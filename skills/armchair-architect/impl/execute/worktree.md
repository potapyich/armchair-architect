# Impl: Execute via Git Worktree

Runs execution in an isolated git worktree — a separate working directory on a feature
branch. Main branch stays clean throughout execution.

To switch to this executor:
```
/armchair-architect use execute worktree
```

---

## Prerequisites

- Git repository with at least one commit
- Clean working tree (no uncommitted changes on main)

---

## Setup

### 1. Determine branch name

Read `prd.md` title or ask the user for a short branch name:
> What branch name should I use? (e.g. `feat/user-auth`, `feat/payment-flow`)

### 2. Create worktree

```bash
BRANCH="<chosen-branch-name>"
git worktree add ../${PWD##*/}-worktree $BRANCH 2>/dev/null || \
git worktree add ../${PWD##*/}-worktree -b $BRANCH
```

Tell the user:
> Created worktree at `../<project>-worktree` on branch `<branch>`.
> All execution happens there — main stays clean.

### 3. Copy implementation_plan.json to worktree

```bash
cp implementation_plan.json ../${PWD##*/}-worktree/implementation_plan.json
```

---

## Execution

Tell the user to switch to the worktree directory and run ralph:

> Open a new Claude Code session in `../<project>-worktree/` and run `/ralph-loop`.
>
> Or: `cd ../<project>-worktree && claude` then `/ralph-loop`.

---

## Completion

When all tasks pass, the user can open a PR from the feature branch:

```bash
cd ../${PWD##*/}-worktree
git push -u origin <branch>
gh pr create --fill
```

To clean up the worktree after merging:
```bash
git worktree remove ../${PWD##*/}-worktree
```

---

## Resuming

Run `/armchair-architect` from the worktree directory (not main) — it will find
`implementation_plan.json` and `state.json` and resume from where execution stopped.
