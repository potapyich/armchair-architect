# Step 03 — Interview Setup

## Goal

Configure the interview mode before starting the interview.

## Instructions

### 1. Present options to the user

Ask:

> Before we start the interview, let's configure it.
>
> **Question limit:** How many questions should I ask?
> - Unlimited (I'll tell you when I'm done)
> - Fixed number: ___
>
> **Mode:**
> - **Chunked / 5 questions (recommended):** I pause every 5 questions, tell you my current
>   confidence level, flag any critical gaps, and offer to continue or stop.
> - **Continuous:** I ask all questions without pausing, then give a summary.
>
> What do you prefer?

### 2. Record configuration

Wait for the user's response. Parse their preferences:
- `interview_mode`: `"chunked_5"` or `"continuous"`
- `interview_limit`: number or `null` (unlimited)

### 3. Update state

Advance pipeline state and record interview configuration:

```bash
PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -c "
import state
s = state.load() or {}
s['interview_mode'] = '<chunked_5 or continuous>'
s['interview_limit'] = None  # or a number
s['interview_questions_asked'] = 0
state.save(s)
state.advance()
"
```

Replace the interview_mode and interview_limit values with the user's choices.

### 4. Transition

Confirm:
> Got it. Starting interview now.

Then immediately begin the interview — load `${CLAUDE_SKILL_DIR}/steps/04_interview.md`.
