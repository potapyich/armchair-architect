# Impl: Critique (Default)

Runs a subagent critic at two points in the pipeline — PRD and implementation plan.
The subagent receives only the document, with no history of how it was generated.

---

## PRD Critique

After generating `prd.md`, run:

```
Agent(prompt="You are a product/tech critic. Find problems in this PRD:

---
[insert full contents of prd.md here]
---

Look for:
- Contradictions or conflicting requirements
- Undefined or ambiguous scope
- Missing edge cases (auth failures, empty states, concurrent access, error handling)
- Absent non-functional requirements (performance, security, scalability)
- Implicit stack or architecture assumptions
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

After generating `implementation_plan.md` and before showing the approval gate, run:

```
Agent(prompt="You are a senior engineer reviewing an implementation plan. Find problems:

---
[insert full contents of implementation_plan.md here]
---

Look for:
- Wrong order of steps (dependency violations)
- Missing steps (things implied but not listed)
- Steps too large for one focused session
- Missing dependencies between blocks
- Incorrect assumptions about existing code or infrastructure
- Verification criteria that can't be checked with a shell command

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
