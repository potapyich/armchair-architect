# Impl: Interview via Ask User Question

## Approach

Ask questions directly in the conversation. One question at a time.
Wait for the user's answer before proceeding to the next question.

## Format

Ask questions in plain conversational text. No forms, no bullet lists of questions at once.

Good:
> What's the expected data volume for the events table — hundreds of rows or millions?

Bad (too many at once):
> 1. What's the data volume?
> 2. Do you need real-time updates?
> 3. What's the auth model?

## Tracking

After each answer:
- Increment `interview_questions_asked` in the active pipeline state file
- Note the answer internally for use in the PRD update

## When to Ask Follow-ups

If an answer is vague or introduces new uncertainty, ask a follow-up before moving on.
Count follow-ups toward the question total.

## Chunked Mode Checkpoint Format

```
--- Checkpoint: Q<N> of <limit|"unlimited"> ---

Confidence: Low / Medium / High

Must resolve before coding:
- <gap>

Can defer:
- <gap>

Continue?
A) 5 more questions
B) 10 more questions
C) Finish — proceed with current understanding
```

Confidence levels:
- **High** — enough detail to write a complete implementation plan without guessing
- **Medium** — main flows clear, some edge cases or technical details unclear
- **Low** — core architecture or major user flows still ambiguous
