# AGENTS.md — armchair-architect

Instructions for AI agents working on this codebase.

## What This Is

A Claude Code plugin implementing a feature development pipeline. No build step, no dependencies.
All logic lives in markdown prompt files interpreted by Claude Code at runtime.

Entry point: `/armchair-architect` → `skills/armchair-architect/SKILL.md`

---

## Architecture

### Two-level abstraction

```
SKILL.md (orchestrator)
    ↓
steps/          ← WHAT each phase does (stable contract)
    ↓
impl/           ← HOW it's done (swappable implementations)
```

**`steps/`** — defines the contract for each pipeline phase. Treat as a stable interface.
Changes here can break existing pipelines mid-run. Only modify with a clear reason.

**`impl/`** — concrete implementations. Freely replaceable. Current impls:
- `impl/interview/ask_user_question.md` — default interview strategy
- `impl/execute/default.md` — built-in executor (no external dependencies)
- `impl/execute/ralph.md` — delegates to ralph-loop plugin
- `impl/execute/tdd.md` — TDD protocol on top of ralph
- `impl/execute/worktree.md` — isolated git worktree per feature, opens PR on completion
- `impl/critique/none.md` — no critic (default)
- `impl/critique/default.md` — subagent critics for PRD and implementation plan
- `impl/critique/strict.md` — same + security/performance angle

### Pipeline steps (in order)

| Step name | File |
|---|---|
| `init` | `steps/01_init.md` |
| `setup` | `steps/02_setup.md` |
| `interview_setup` | `steps/03_interview_setup.md` |
| `interview` | `steps/04_interview.md` |
| `plan` | `steps/05_plan.md` |
| `impl_plan` | `steps/06_impl_plan.md` |
| `execute` | `steps/07_execute.md` |

### Runtime state

`.pipeline/<feature>/state.json` lives in the **user's project**, not in this repo.
The active pipeline name is stored in `.pipeline/active`.
Both are gitignored in user projects.

Full schema:

```json
{
  "step": "interview",
  "lang": "ru",
  "interview_mode": "chunked_5",
  "interview_questions_asked": 7,
  "completed": ["init", "setup", "interview_setup"],
  "pending": ["interview", "plan", "impl_plan", "execute"],
  "impl": {
    "interview": "ask_user_question",
    "execute": "default",
    "critique": "none",
    "review_every": 0
  }
}
```

`impl.review_every`: 0 = off, N = run a subagent code review every N completed tasks.

### implementation_plan.json schema

```json
{
  "id": "1.1",
  "category": "backend|frontend|database|infra|test|config",
  "description": "...",
  "context": "...",
  "verification": ["npm test -- --grep 'name'", "curl http://localhost:3000/health"],
  "dependsOn": [],
  "parallel": false,
  "group": "",
  "passes": false,
  "in_progress": false
}
```

- `dependsOn`: task ids that must pass before this task can start
- `parallel` + `group`: tasks sharing a group with `parallel: true` are launched concurrently via Agent tool
- `in_progress`: set before implementation starts, cleared on pass or stuck — enables restart recovery

### Shell injection

Live data is injected into prompts via:
```
!`command`
```

SKILL.md reads the active pipeline dynamically:
```
!`ACTIVE=$(cat .pipeline/active 2>/dev/null || echo 'default'); cat .pipeline/$ACTIVE/state.json 2>/dev/null || echo '{...}'`
```

This is the only mechanism for reading runtime state into a prompt. Do not replace it with static values.

All python3 state snippets in step files use the same active-pipeline pattern:
```python
import os as _os
_active = open('.pipeline/active').read().strip() if _os.path.exists('.pipeline/active') else 'default'
_sp = f'.pipeline/{_active}/state.json'
```

---

## Rules When Editing

1. **No hardcoded paths.** Use `${CLAUDE_SKILL_DIR}` to reference files within the skill directory.
   Wrong: `Read skills/armchair-architect/steps/01_init.md`
   Right: `Read ${CLAUDE_SKILL_DIR}/steps/01_init.md`

2. **No build step, no dependencies.** Do not add package.json, requirements.txt, or any toolchain.

3. **Russian `*_ru.md` files are primary for Russian users.** `prd_ru.md`, `plan_ru.md`,
   `implementation_plan_ru.md` are what the user reads and approves. English versions are derived
   from confirmed Russian. For English users, only English versions exist.

4. **Steps are a stable contract.** If you change what a step produces or expects, check whether
   `state.json` schema or the SKILL.md routing table also needs updating.

5. **SKILL.md routing table must stay in sync** with step files. If you add or rename a step,
   update both the routing table in `SKILL.md` and the step files that advance state.

6. **State path is always dynamic.** Never hardcode `.pipeline/state.json` — always resolve
   through `.pipeline/active` first.

---

## What NOT to Do

- Do not create `.pipeline/` files in this repo — they belong in user projects
- Do not edit `*_ru.md` files directly in this repo
- Do not add abstractions for one-off operations
- Do not add error handling for cases that cannot happen in normal Claude Code execution
- Do not change the `steps/` interface without a strong reason — pipelines in progress depend on it
- Do not hardcode `.pipeline/state.json` — use the active pipeline path pattern

---

## Testing a Change

1. Copy or symlink `skills/armchair-architect/` to `~/.claude/skills/armchair-architect/`
2. Open a test project in Claude Code
3. Run `/armchair-architect status` — should show state or empty init state
4. Run `/armchair-architect` — should propose the next step or start init

Alternatively, configure as a plugin in `~/.claude/settings.json`:
```json
{ "plugins": ["/path/to/armchair-architect"] }
```

There are no automated tests. Verification is manual and interactive.

---

## Key Files in This Repo

| File | Purpose |
|---|---|
| `SKILL.md` | Entry point, orchestrator, and all routing logic |
| `steps/NN_<name>.md` | Step contracts (WHAT) |
| `impl/<component>/<name>.md` | Step implementations (HOW) |
| `DESIGN.md` | Full architecture and design decisions |
| `CLAUDE.md` | Instructions for Claude Code working on this repo |
