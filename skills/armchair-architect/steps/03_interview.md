# Step 03 — Interview

## Goal

Deepen the PRD through targeted questions until it's detailed enough for any senior engineer
to implement without clarification.

## Interview Focus Areas

Prioritize questions about:
- **Technical tradeoffs** — why this stack/approach over alternatives?
- **Edge cases** — what happens when X fails, is empty, is concurrent?
- **Architectural decisions** — where does state live? how do components communicate?
- **UI/UX details** — exact flows, error states, empty states, loading states
- **Things the user may not have considered** — scalability, auth, data migration, rollback
- **Integration constraints** — external APIs, rate limits, existing systems
- **Definition of done** — how will we know each piece is complete?

Do NOT ask about things already answered in `prd.md` or `CLAUDE.md`.

## Interview Execution

### Read current state

Check `interview_mode`, `interview_questions_asked`, and `critique_prd` from state.

If `critique_prd` is a non-empty array: use those findings as the first questions of the
interview (they are pre-identified gaps). Count them toward `interview_questions_asked`.

### Ask questions

Ask one question at a time. Wait for the answer before asking the next.

After each answer: increment `interview_questions_asked` in state.

### Chunked mode (chunked_5)

After every 5 questions, pause and give an assessment:

```
--- Interview checkpoint (Q<N>) ---

Confidence: <Low / Medium / High>

Critical gaps remaining (must resolve before coding):
- <gap 1>
- <gap 2>

Deferrable gaps (can clarify during implementation):
- <gap 1>

Options:
A) Continue — 5 more questions
B) Continue — 10 more questions
C) Finish interview — proceed with current understanding
D) I'm done, let's proceed
```

Be honest about confidence. Do not say "High" unless you genuinely have enough to write
a complete implementation plan.

### Limit enforcement

If `interview_limit` is set and `interview_questions_asked >= interview_limit`:
- Give a final assessment (same format as checkpoint)
- Proceed to wrap-up

### Continuous mode

Ask all questions, then give one final assessment at the end.

## Wrap-up

When the interview is complete (user chose to finish or limit reached):

1. Summarize key decisions made during the interview
2. Update `prd.md` with all clarifications — add detail, resolve "Open Questions" section
3. If `lang = "ru"`, regenerate `_prd_ru.md` from updated `prd.md`
4. Update state — advance pipeline:

```bash
python3 -c "
import json
with open('.pipeline/state.json') as f: s = json.load(f)
cur = s['step']
s['completed'] = s.get('completed', []) + [cur]
s['pending'] = [x for x in s.get('pending', []) if x != cur]
s['step'] = s['pending'][0] if s['pending'] else 'done'
with open('.pipeline/state.json', 'w') as f: json.dump(s, f, indent=2)
"
```

5. Confirm:
> Interview complete. PRD updated. Ready to generate the strategy plan — run `/armchair-architect` to continue.
