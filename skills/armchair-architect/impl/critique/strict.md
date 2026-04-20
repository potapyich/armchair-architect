# Impl: Critique (Strict)

Same as default, but with additional focus areas: security, performance, and operational concerns.

---

## PRD Critique

After generating `prd.md`, run:

```
Agent(prompt="You are a senior security and systems engineer. Find problems in this PRD:

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
- Implicit stack or architecture assumptions
- Anything that would cause a senior engineer to stop and ask a question mid-implementation

Output a numbered list of specific problems grouped by severity (Critical / Important / Minor).
Be direct. No praise, no filler.")
```

Show findings labeled **Critic's notes (strict mode)**. Save to `critique_prd` in state.

---

## Implementation Plan Critique

After generating `implementation_plan.md`, run:

```
Agent(prompt="You are a senior engineer and security reviewer. Find problems in this plan:

---
[insert full contents of implementation_plan.md here]
---

Look for ALL of the following:
- Wrong order of steps (dependency violations)
- Missing steps (things implied but not listed)
- Steps too large for one focused session
- Missing dependencies between blocks
- Security issues introduced by the implementation approach
- Missing test coverage for critical paths
- Verification criteria that can't be checked with a shell command
- Performance bottlenecks baked into the design
- Missing error handling or rollback steps

Output a numbered list of specific problems grouped by severity (Critical / Important / Minor).
Be direct. No praise, no filler.")
```

Show: implementation plan + critic findings (grouped by severity) + approval gate.
