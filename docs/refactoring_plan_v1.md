# Development Plan v1

Architecture review of the MVP + ideas for next iterations.

---

## What Works Well

**Right problem.** The core pain of LLM codegen is "jumped into code without context."
Pipeline enforces PRD → interview → plan → impl plan → tasks → execute. Reduces rewrites.

**Two-level abstraction (steps/ vs impl/).** Best architectural decision in the codebase.
Separating "what to do" (steps/) from "how to do it" (impl/) enables:
- Swapping executors (ralph ↔ default) without touching the pipeline
- Plugging in alternative interview modes (MCP-based, form-based)
- Changing "how" without breaking the step contract

**Approval gates.** Gates on plan and impl_plan are critical. Without them the LLM runs on
its own interpretation. Forced pause for user review is what separates useful pipeline from
a dangerous one.

**Zero-dependency.** No runtime beyond Claude Code. Pure markdown. Install = git clone +
one line in settings.json. Minimal friction.

**Shell injection for state.** `` !`cat .pipeline/state.json 2>/dev/null || echo '{}'` ``
is elegant. Native Claude Code mechanism for injecting live data into prompts. Reliable,
no custom runtime needed.

**Default executor (embedded).** Not depending on ralph is the right default. Progressive
disclosure: works out of the box, ralph is the advanced option.

**Verification as shell commands.** `verification: ["npm test ...", "curl ..."]` makes
execution verifiable. Exit code 0/non-0 is a simple and reliable contract.

**Stuck task handling.** 2 attempts → propose split → user approval. Doesn't silently fail,
doesn't loop, doesn't change scope without asking.

---

## What's Fragile

### 1. Linear pipeline — main limitation

Hard sequence: init → interview → plan → impl_plan → tasks → execute.
In practice:
- After plan, often need to revisit PRD (realized it was wrong)
- After executing 3 tasks, discover plan needs to change
- Interview may be unnecessary (user arrives with a ready PRD)

Only way to "go back" today: reset and start over. No `goto`, no `back`, no partial rollback.
Acceptable for MVP, but the first thing that will start causing friction.

### 2. State management is fragile

Each step file hardcodes the full expected state JSON:
```json
{
  "step": "plan",
  "completed": ["init", "interview_setup", "interview"],
  "pending": ["plan", "impl_plan", "tasks", "execute"]
}
```
Add or remove a step → must update JSON in all subsequent step files. No single source of
truth for step sequence. SKILL.md has a step table, but step files duplicate the sequence.

### 3. One pipeline = one feature

No support for multiple parallel pipelines (e.g., feature A in execute, feature B in
interview). State lives in one `.pipeline/state.json`. Will become a bottleneck on larger
projects with multiple concurrent features.

### 4. No state validation

Nothing checks that `state.json` is consistent. Manual edits or corruption can put the
pipeline in an invalid state. LLM will try to interpret garbage.

### 5. Context budget detection is approximate

"At ~40-50% estimated usage" — Claude has no precise API for measuring context usage. This
will work as a rough heuristic at best. Especially relevant for the default executor, which
runs in the same session.

### 6. No feedback loop from execution to planning

If execution reveals that the architectural approach is wrong, pipeline doesn't have an
"escalate to plan" path — only stuck task split. Sometimes you need to change `plan.md`,
not subdivide a task.

### 7. Interview UX — no fast path

One question at a time is right for depth, but for large projects: 20-30 questions × wait
for answer. No fast path for experienced users who can dump architecture docs, existing
ADRs, or a full technical spec upfront and skip interview.

### 8. `implementation_plan.json` is a flat list

No explicit dependencies between tasks (only implicit ordering). If task 3.1 depends on
2.3, it's not expressed anywhere. Sequential execution works, but no support for
reordering or parallelization if needed.

### 9. Ralph integration is manual handoff

"Tell the user to run /ralph-loop" is an instruction, not an integration. Noticeable
friction: user must manually switch between two skills.

> **Status:** not solvable on our side — waiting for skill-to-skill API from Claude Code.
> Removed from active backlog.

### 10. Steps are not idempotent

If pipeline interrupted mid-step (network error, context overflow), re-running
`/armchair-architect` restarts the step from scratch. For init/interview this is tolerable.
For execute — partial code changes + restart may create conflicts.

### 11. Bilingual artifacts drift between phases

`prd_ru.md`, `plan_ru.md`, `implementation_plan_ru.md` — now primary documents for Russian
users. English versions (`prd.md` etc.) are derived from confirmed Russian, not the other
way around. English users get no Russian versions.

---

## Scores

| Dimension | Score | Notes |
|---|---|---|
| Idea | 8/10 | Right problem, right approach, good abstraction level |
| Technical | 7/10 | Strong for pure-markdown MVP; fragility is in state management and linear flow |

Main risk: pipeline linearity will start causing friction on real projects.

---

## New Capabilities

### Context7 onboarding

Context7 — MCP plugin with up-to-date library documentation. Enabled globally by the
author; may be missing on a new machine.

**Onboarding in `steps/01_init.md`:**

```
Check for context7:
!`cat ~/.claude/settings.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok' if d.get('enabledPlugins',{}).get('context7@claude-plugins-official') else 'missing')" 2>/dev/null || echo "missing"`
```

If `missing` — offer to the user:
> Context7 is not installed. It's an MCP plugin with up-to-date library documentation —
> helps write correct code for current dependency versions. Add it? [y/n]

If yes: append `"context7@claude-plugins-official": true` to `enabledPlugins` in
`~/.claude/settings.json`. Requires session restart to activate.

**Usage in step files:**

`steps/05_impl_plan.md` — when decomposing into tasks:
> If MCP context7 is available — use it for up-to-date dependency documentation
> before describing specific API calls in tasks.

`steps/07_execute.md` — before executing a task:
> If a task uses an external library and context7 is available — check the current API
> before writing code.

Principle: soft recommendation (`if available`), no hard dependency.

---

### Critic layer

Two subagent critics at different pipeline points — clean context, no generation history.

```
PRD → [CRITIC → feeds interview] → interview → plan → impl_plan → [CRITIC] → tasks → execute
```

**PRD critic (after `01_init.md`)**

Most valuable point: a requirements mistake propagates through every downstream phase.

Catches: contradictions, undefined scope, missing edge cases, absent non-functional
requirements (auth, error handling, perf), implicit stack assumptions.

Key bonus: findings become the starting question list for interview.
Result saved to `state.json` as `critique_prd`.

```
Agent(prompt="You are a product/tech critic. Find problems in this PRD:
[contents of prd.md]
Look for: contradictions, undefined scope, missing edge cases,
absent non-functional requirements, implicit assumptions.
Output a numbered list of specific problems. No praise.")
```

**impl_plan critic (after `05_impl_plan.md`)**

Detailed technical review before task slicing — cheap to fix, before execute.

Catches: wrong step order, missing block dependencies, tasks too large for one context
window, wrong assumptions about existing code.

Result shown to user alongside the approval gate.

```
Agent(prompt="You are a senior engineer. Find problems in this implementation plan:
[contents of implementation_plan.md]
Look for: wrong order, missing steps, tasks too large, missing dependencies,
wrong stack assumptions.
Output a numbered list of specific problems. No praise.")
```

Do not add a critic after `plan.md` — low ROI, impl_plan critic follows shortly.

**Impl/ variations:**

| Impl | Behavior |
|---|---|
| `impl/critique/default.md` | Both critics (PRD + impl_plan) |
| `impl/critique/strict.md` | Stricter: security/perf angle, more questions |
| `impl/critique/none.md` | Disable (fast iterations) |

Enable with: `/armchair-architect use critique strict`

---

### TDD gate

Optional step between `tasks` and `execute`. User is asked:
> Use TDD mode? (tests → implementation → refactor for each task) [y/n]

If yes — `impl` switches to `tdd`, state is updated.

**Important:** TDD executor is an injection of TDD protocol on top of ralph, not a
replacement. Default executor is unsuitable for TDD: by the execute phase the context
is already filled with interview/planning history. Ralph runs each task in a fresh session.

`impl/execute/tdd.md` = ralph.md + task extension:

```json
{
  "id": "task-03",
  "description": "...",
  "tdd": {
    "tests_first": "Write failing tests before writing the implementation",
    "verify_red": "npm test -- --testPathPattern=task03 must fail",
    "verify_green": "npm test -- --testPathPattern=task03 must pass"
  }
}
```

Enable with: `/armchair-architect use execute tdd` (requires ralph-loop)

---

### Git worktrees executor

New `impl/execute/worktree.md`:
- Creates an isolated git worktree for the feature branch before execute
- Runs tasks in it, opens PR on success
- Value: no risk of contaminating main branch with partially executed tasks

---

### Parallel subagents

Extension to `implementation_plan.json` schema:
```json
{ "id": "task-03", "parallel": true, "group": "api-layer" }
```
Tasks with the same `group` + `parallel: true` → launched via Agent tool simultaneously.
Implemented in `impl/execute/` without touching `steps/`.

---

### armchair-architect-lite

New skill `skills/armchair-architect-lite/SKILL.md` — single file, no state machine.
Compatible with GitHub Copilot (`.github/skills/`) and Cursor.
Goal: 60–70% of the value via a structured prompt without pipeline machinery.

Lost: state persistence, swappable impl/, ralph executor, enforcement gates.
Preserved: PRD → interview → plan → impl → execute structure, chunked interview, language settings.

---

### Other pipeline improvements

**`/armchair-architect back`** — return to the previous step without full reset.
New routing case in `SKILL.md`: pop last completed, push back to pending.

**Skip paths** — `/armchair-architect skip interview` / `skip planning`.
Routing in `SKILL.md`: check for artifact file and jump over the step.

**Context handoff** — auto-detect ~40% context usage (heuristic): write `progress.md`,
suggest starting a new session.

**Ralphex executor** — `impl/execute/ralphex.md`; placeholder until API stabilizes.

**Code review gate** — every N tasks in execute impl: pause and review pass.
Configurable via state.json.

---

## Roadmap

### P1 — Quick wins (low complexity, high impact)

1. ✅ **`back` command** — new routing case in SKILL.md
2. ✅ **Skip paths** — `skip interview` / `skip planning` in SKILL.md
3. ✅ **Context7 onboarding** — check + offer to install in `02_setup.md`; recommendation in `06_impl_plan.md` and `07_execute.md`

### P2 — Architectural improvements

4. ✅ **Centralized step registry** — remove hardcoded state JSON from each step file
5. ✅ **Critic layer** — `impl/critique/`: two subagent critics (PRD + impl_plan)
6. ✅ **armchair-architect-lite** — for Copilot/Cursor
7. ✅ **TDD gate executor** — `impl/execute/tdd.md` on top of ralph
8. ✅ **Git worktrees executor** — `impl/execute/worktree.md`

### Additionally implemented (outside original plan)

- ✅ **`list` command** — list available impl variants
- ✅ **`setup` step (02_setup.md)** — context7, critique mode, TDD mode in one place
- ✅ **Bilingual order flip** — `prd_ru.md` is primary for ru, `prd.md` derived from it
- ✅ **impl_plan + tasks merged** — JSON generated immediately after markdown approval

### P3 — Complex / deferred

9. ✅ **Parallel subagents** — `parallel`/`group` in JSON schema + Agent tool in executor
9b. **Specialized agents** — when launching parallel tasks, pick prompt by `category` (backend/frontend/database). New `impl/execute/specialized.md` on top of parallel executor. No changes to `steps/`.
10. **Multi-pipeline support** — `.pipeline/<feature>/state.json`
11. ✅ **Context handoff** — auto-detect ~40% context usage, write progress.md
12. ✅ **Code review gate** — pause every N tasks in execute
13. **Interview fast path** — accept document dump, skip to confirmation
14. ✅ **Escalation execution → planning** — "this task revealed a plan-level problem"
15. ✅ **Task dependencies in JSON schema** — explicit `dependsOn` field
16. ✅ **State validation** — basic schema check on load
17. ✅ **Step idempotency** — handle mid-step restarts cleanly in execute
18. **Ralphex executor** — `impl/execute/ralphex.md`; waiting for API stabilization

---

## What Not to Change

- Shell injection for state (`!` preprocessing) — keep as-is, it works
- steps/impl two-level abstraction — core architectural strength, don't collapse
- Approval gates on plan and impl_plan — non-negotiable
- Zero-dependency philosophy — no build steps, no external runtime
