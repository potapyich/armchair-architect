# AGENTS.md — doit-cc-plugin

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
- `impl/execute/default.md` — default executor
- `impl/execute/ralph.md` — ralph-based executor

### Pipeline steps (in order)

| Step name | File |
|---|---|
| `init` | `steps/01_init.md` |
| `interview_setup` | `steps/02_interview_setup.md` |
| `interview` | `steps/03_interview.md` |
| `plan` | `steps/04_plan.md` |
| `impl_plan` | `steps/05_impl_plan.md` |
| `tasks` | `steps/06_tasks.md` |
| `execute` | `steps/07_execute.md` |

### Runtime state

`.pipeline/state.json` lives in the **user's project**, not in this repo. It is gitignored there.
Schema:

```json
{
  "step": "interview",
  "lang": "ru",
  "interview_mode": "chunked_5",
  "interview_questions_asked": 7,
  "completed": ["init", "interview_setup"],
  "pending": ["interview", "plan", "impl_plan", "tasks", "execute"],
  "impl": {
    "interview": "ask_user_question",
    "execute": "ralph"
  }
}
```

### Shell injection

Live data is injected into prompts via:
```
!`command`
```
Example in `SKILL.md`:
```
!`cat .pipeline/state.json 2>/dev/null || echo '{...}'`
```
This is the only mechanism for reading runtime state into a prompt. Do not replace it with static values.

---

## Rules When Editing

1. **No hardcoded paths.** Use `${CLAUDE_SKILL_DIR}` to reference files within the skill directory.
   Wrong: `Read skills/armchair-architect/steps/01_init.md`
   Right: `Read ${CLAUDE_SKILL_DIR}/steps/01_init.md`

2. **No build step, no dependencies.** This is intentional. Do not add package.json, requirements.txt,
   or any toolchain. If a change requires a build step, reconsider the approach.

3. **Russian `*_ru.md` files are primary for Russian users.** Files like `prd_ru.md`, `plan_ru.md`
   are the documents the user reads and approves. English versions (`prd.md`, `plan.md`) are derived
   from confirmed Russian. For English users, only the English versions exist. Do not modify these
   files directly in this repo.

4. **Steps are a stable contract.** If you change what a step produces or expects, check whether
   `state.json` schema or the SKILL.md routing table also needs updating.

5. **SKILL.md routing table must stay in sync** with the step files in `steps/`. If you add or rename
   a step, update both the routing table in `SKILL.md` and the step files.

---

## What NOT to Do

- Do not create `.pipeline/state.json` in this repo — it belongs in user projects
- Do not edit `*_ru.md` files directly in this repo
- Do not add abstractions for one-off operations
- Do not add error handling for cases that cannot happen in normal Claude Code execution
- Do not change the `steps/` interface without a strong reason — pipelines in progress depend on it

---

## Testing a Change

1. Copy or symlink `skills/armchair-architect/` to `~/.claude/skills/armchair-architect/`
2. Open a test project in Claude Code
3. Run `/armchair-architect status` — should show state or empty init state
4. Run `/armchair-architect` — should propose the next step or start init

Alternatively, configure as a plugin in `~/.claude/settings.json`:
```json
{ "plugins": ["/path/to/doit-cc-plugin"] }
```

There are no automated tests. Verification is manual and interactive.

---

## Key Files in This Repo

| File | Purpose |
|---|---|
| `SKILL.md` | Entry point and orchestrator |
| `steps/NN_<name>.md` | Step contracts (WHAT) |
| `impl/<component>/<name>.md` | Step implementations (HOW) |
| `DESIGN.md` | Full architecture and design decisions |
| `CLAUDE.md` | Instructions for Claude Code working on this repo |
