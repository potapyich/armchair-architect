# Impl: Critique (Default)

Runs a subagent critic at two points in the pipeline — PRD and implementation plan.
The subagent receives only the document, with no history of how it was generated.

---

## PRD Critique

After generating `prd.md`, read `CLAUDE.md` if it exists (it carries the project's stack
and conventions — the critic should ground findings in this context).

```bash
[ -f CLAUDE.md ] && cat CLAUDE.md || echo "(no CLAUDE.md present)"
```

Then run:

```
Agent(prompt="You are a product/tech critic. Find problems in this PRD.

Project context (from CLAUDE.md, may be empty):
---
[insert contents of CLAUDE.md, or '(no CLAUDE.md)' if absent]
---

PRD to critique:
---
[insert full contents of prd.md here]
---

Look for:
- Contradictions or conflicting requirements
- Undefined or ambiguous scope
- Missing edge cases (auth failures, empty states, concurrent access, error handling)
- Absent non-functional requirements (performance, security, scalability)
- Implicit stack or architecture assumptions — flag any that conflict with CLAUDE.md
- Anything that would cause a senior engineer to stop and ask a question mid-implementation

Output a numbered list of specific problems. Be direct. No praise, no filler.")
```

If the subagent returns findings:
- Show them to the user labeled as **Critic's notes on the PRD**
- Save the findings to state as `critique_prd` (array of strings, one per finding)
- These become starting input for the interview step

If no findings: save `critique_prd: []` and continue silently.

---

## Implementation Plan Critique

After generating `implementation_plan.md` and before showing the approval gate, read
`CLAUDE.md` and the approved `prd.md` (the critic needs both to evaluate whether the plan
matches the requirements and the project's actual stack):

```bash
[ -f CLAUDE.md ] && cat CLAUDE.md || echo "(no CLAUDE.md present)"
cat prd.md
```

Then run:

```
Agent(prompt="You are a senior engineer reviewing an implementation plan. Find problems.

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

Look for:
- Wrong order of steps (dependency violations)
- Missing steps (things implied by the PRD but not listed in the plan)
- Steps too large for one focused session
- Missing dependencies between blocks
- Incorrect assumptions about existing code or infrastructure (cross-check with CLAUDE.md)
- Verification criteria that can't be checked with a shell command
- Plan items that don't trace back to a PRD requirement (scope creep)

Output a numbered list of specific problems. Be direct. No praise, no filler.")
```

Show the user: implementation plan + critic findings + approval gate together:

> **Implementation Plan** *(above)*
>
> **Critic's notes:**
> 1. <finding>
> 2. <finding>
>
> Approve as-is, or tell me what to fix?
