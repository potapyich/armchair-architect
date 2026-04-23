# Impl: Critique (Strict)

Same as default, but with additional focus areas: security, performance, and operational concerns.

---

## PRD Critique

Read `CLAUDE.md` first — strict mode tailors security and performance findings to the
project's actual stack:

```bash
[ -f CLAUDE.md ] && cat CLAUDE.md || echo "(no CLAUDE.md present)"
```

Then run:

```
Agent(prompt="You are a senior security and systems engineer. Find problems in this PRD.

Project context (from CLAUDE.md, may be empty):
---
[insert contents of CLAUDE.md, or '(no CLAUDE.md)' if absent]
---

PRD to critique:
---
[insert full contents of prd.md here]
---

Look for ALL of the following:
- Contradictions or conflicting requirements
- Undefined or ambiguous scope
- Missing edge cases (auth failures, empty states, concurrent access, error handling)
- Absent non-functional requirements (performance targets, SLAs, data retention)
- Security gaps: missing auth/authz, injection risks, sensitive data handling, audit logging
- Operational gaps: no monitoring/alerting plan, no rollback strategy, no migration plan
- Scalability assumptions that may not hold
- Stack-specific risks — if CLAUDE.md names a runtime/framework, channel security and
  performance findings through that lens (e.g., Node.js → async/event-loop pitfalls;
  Python → GIL/concurrency model; PostgreSQL → connection pool sizing, lock contention)
- Implicit stack or architecture assumptions that conflict with CLAUDE.md
- Anything that would cause a senior engineer to stop and ask a question mid-implementation

Output a numbered list of specific problems grouped by severity (Critical / Important / Minor).
Be direct. No praise, no filler.")
```

Show findings labeled **Critic's notes (strict mode)**. Save to `critique_prd` in state.

---

## Implementation Plan Critique

Read `CLAUDE.md` and the approved `prd.md` so the critic can check both fit-for-stack
and fit-for-requirements:

```bash
[ -f CLAUDE.md ] && cat CLAUDE.md || echo "(no CLAUDE.md present)"
cat prd.md
```

Then run:

```
Agent(prompt="You are a senior engineer and security reviewer. Find problems in this plan.

Project context (from CLAUDE.md, may be empty):
---
[insert contents of CLAUDE.md, or '(no CLAUDE.md)' if absent]
---

Approved PRD:
---
[insert contents of prd.md]
---

Implementation plan to critique:
---
[insert full contents of implementation_plan.md]
---

Look for ALL of the following:
- Wrong order of steps (dependency violations)
- Missing steps (things implied by the PRD but not listed)
- Steps too large for one focused session
- Missing dependencies between blocks
- Security issues introduced by the implementation approach (channel through CLAUDE.md stack)
- Missing test coverage for critical paths
- Verification criteria that can't be checked with a shell command
- Performance bottlenecks baked into the design
- Missing error handling or rollback steps
- Plan items that don't trace back to a PRD requirement (scope creep)

Output a numbered list of specific problems grouped by severity (Critical / Important / Minor).
Be direct. No praise, no filler.")
```

Show: implementation plan + critic findings (grouped by severity) + approval gate.
