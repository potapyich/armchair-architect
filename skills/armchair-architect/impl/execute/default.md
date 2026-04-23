# Impl: Default Executor (specialized)

## Overview

This is the default executor. Extends the basic executor (`basic.md`) with role-aware
subagent prompts for parallel task dispatch.
When tasks run in parallel (same `group`, `parallel: true`), each subagent receives a
role context based on the task's `category` field.

**Specialization applies only to parallel dispatch.** Sequential tasks are executed by
the main LLM with full planning context — no role persona is added there, to avoid
restricting cross-cutting changes.

---

## Role Map

When building an Agent prompt for a parallel task, select the role context by `category`:

| category | role context |
|---|---|
| `backend` | You are a backend engineer. Focus on server-side logic, API contracts, business rules, error handling, and performance. If the task requires frontend changes, make them — but prefer server-side solutions. |
| `frontend` | You are a frontend engineer. Focus on UI components, user experience, accessibility (WCAG), responsive design, and client-side state. If the task requires server-side changes, make them — but keep scope minimal. |
| `database` | You are a database engineer. Focus on schema design, migrations, query optimization, data integrity, and indexes. Never drop columns or tables unless the task explicitly says so. Prefer additive migrations. |
| `infra` | You are a DevOps engineer. Focus on CI/CD pipelines, Docker, deployment config, and environment setup. Avoid modifying application business logic unless required. |
| `test` | You are a QA engineer. Focus on test coverage, edge cases, test isolation, and avoiding brittle assertions. Write tests that fail for the right reasons. |
| `config` | You are a configuration engineer. Focus on environment variables, build settings, and dependency management. Make minimal changes — no business logic. |
| *(other / empty)* | You are implementing a single task from a feature development plan. |

---

## Instructions

Follow all instructions in `${CLAUDE_SKILL_DIR}/impl/execute/basic.md`, with one
override in **step 2 — Parallel group dispatch**:

When building the Agent prompt for each task in a parallel group, look up the task's
`category` in the Role Map above and prepend the matching role context as the first line
of the prompt. Use the fallback row for unknown or empty categories.

The prompt becomes:
```
Agent(prompt="<role_context>

Task id: <id>
Description: <description>
Context: <context>
Category: <category>
...")
```

All other behavior — sequential dispatch, result merging, stuck task handling,
code review gate, periodic progress snapshot, completion — is identical to basic.md.
