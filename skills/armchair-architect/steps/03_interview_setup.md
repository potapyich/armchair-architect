# Step 02 — Interview Setup

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
python3 -c "
import json
import os as _os; _active = open('.pipeline/active').read().strip() if _os.path.exists('.pipeline/active') else 'default'; _sp = f'.pipeline/{_active}/state.json'
with open(_sp) as f: s = json.load(f)
cur = s['step']
s['completed'] = s.get('completed', []) + [cur]
s['pending'] = [x for x in s.get('pending', []) if x != cur]
s['step'] = s['pending'][0] if s['pending'] else 'done'
s['interview_mode'] = '<chunked_5 or continuous>'
s['interview_limit'] = None  # or a number
s['interview_questions_asked'] = 0
with open(_sp, 'w') as f: json.dump(s, f, indent=2)
"
```

Replace the interview_mode and interview_limit values with the user's choices.

### 4. Transition

Confirm:
> Got it. Starting interview now.

Then immediately begin Step 03 (interview) — load `${CLAUDE_SKILL_DIR}/steps/03_interview.md`.
