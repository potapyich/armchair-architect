# Implementation Plan v2

Детальный план имплементации [refactoring_plan_v2_ru.md](./refactoring_plan_v2_ru.md).
Каждый блок самодостаточен — можно делать в любом порядке (кроме явно указанных зависимостей).

Оценка времени дана для разработчика, знакомого с проектом, без дебага окружения.

---

## Block 1: Quick fixes (≈30 минут суммарно)

Можно делать одной PR. Зависимостей между ними нет.

### 1.1 Фикс отступов в escalation rollback

**Файл:** [skills/armchair-architect/impl/execute/default.md:301-313](../skills/armchair-architect/impl/execute/default.md)

**Проблема:** строка 304 `with open(_sp) as f: s = json.load(f)` стоит без отступа, остальной блок с отступом 5 пробелов. При запуске даст `IndentationError`.

**Что сделать:** заменить весь блок единым корректно отформатированным `python3 -c`.

**До:**
```bash
     python3 -c "
     import json
     import os as _os; _active = open('.pipeline/active').read().strip() if _os.path.exists('.pipeline/active') else 'default'; _sp = f'.pipeline/{_active}/state.json'
with open(_sp) as f: s = json.load(f)
     target = '<chosen_step>'
     all_steps = ['init','setup','interview_setup','interview','plan','impl_plan','execute']
     target_idx = all_steps.index(target)
     to_rollback = [x for x in s.get('completed', []) if all_steps.index(x) >= target_idx]
     s['completed'] = [x for x in s.get('completed', []) if x not in to_rollback]
     s['pending'] = to_rollback + s.get('pending', [])
     s['step'] = target
     with open(_sp, 'w') as f: json.dump(s, f, indent=2)
     "
```

**После:** убрать ведущие 5 пробелов у всех Python-строк, чтобы они были на колонке 0:
```bash
python3 -c "
import json, os
active = open('.pipeline/active').read().strip() if os.path.exists('.pipeline/active') else 'default'
sp = f'.pipeline/{active}/state.json'
with open(sp) as f: s = json.load(f)
target = '<chosen_step>'
all_steps = ['init','setup','interview_setup','interview','plan','impl_plan','execute']
target_idx = all_steps.index(target)
to_rollback = [x for x in s.get('completed', []) if all_steps.index(x) >= target_idx]
s['completed'] = [x for x in s.get('completed', []) if x not in to_rollback]
s['pending'] = to_rollback + s.get('pending', [])
s['step'] = target
with open(sp, 'w') as f: json.dump(s, f, indent=2)
"
```

Заметь: в Python отступ важен только относительно начала логического блока. Markdown сам по себе не влияет, но markdown-list-item конвертирует ведущие пробелы в часть code-блока, что и сломало отступ.

**Verification:**
```bash
python3 -c "$(sed -n '/python3 -c \"/,/^\"$/p' skills/armchair-architect/impl/execute/default.md | sed '1d;$d')" --check
```
Не должно бросить `IndentationError`. Полное end-to-end тестирование возможно только через реальный запуск escalation в pipeline.

**Время:** 5 минут.

---

### 1.2 Привести в порядок заголовки шагов

**Проблема:** после переименования файлов 4 из 7 файлов имеют расхождение filename ↔ header.

| Файл | Сейчас | Должно быть |
|---|---|---|
| `steps/03_interview_setup.md` | `# Step 02 — Interview Setup` | `# Step 03 — Interview Setup` |
| `steps/04_interview.md` | `# Step 03 — Interview` | `# Step 04 — Interview` |
| `steps/05_plan.md` | `# Step 04 — Strategy Plan` | `# Step 05 — Strategy Plan` |
| `steps/06_impl_plan.md` | `# Step 05 — Implementation Plan & Tasks` | `# Step 06 — Implementation Plan & Tasks` |

**Что сделать:** Edit в каждом файле первой строки.

**Verification:**
```bash
for f in skills/armchair-architect/steps/*.md; do
  num=$(basename "$f" | grep -oE '^[0-9]+')
  header=$(head -1 "$f" | grep -oE 'Step [0-9]+' | grep -oE '[0-9]+')
  [ "$num" = "$header" ] || echo "MISMATCH: $f (file=$num header=$header)"
done
```
Должно быть тихо.

**Время:** 5 минут.

---

### 1.3 Off-by-one в нумерации секций `06_impl_plan.md`

**Файл:** [skills/armchair-architect/steps/06_impl_plan.md:142](../skills/armchair-architect/steps/06_impl_plan.md)

**Проблема:** секция `### 8. Generate implementation_plan.json` (строка 89) → следующая `### 10. Show summary` (строка 142). Пропущен `### 9`.

**Что сделать:** переименовать `### 10. Show summary` → `### 9. Show summary` и `### 11. Update state` → `### 10. Update state`.

**Время:** 2 минуты.

---

### 1.4 Удалить misleading "~40-50%" из step и impl файлов

**Проблема:** Claude не выдаёт точную метрику context usage. Текущие "At ~40-50% estimated usage" в [steps/07_execute.md:58](../skills/armchair-architect/steps/07_execute.md) и [impl/execute/default.md:323](../skills/armchair-architect/impl/execute/default.md) — это фейк-фича. Будет либо игнорироваться, либо срабатывать неконсистентно.

**Что сделать:** заменить на честную фразу-фоллбек:

**До:**
> If you notice you're approaching context limits (~40-50%), warn the user

**После:**
> Context usage is not directly observable. Treat the following as a soft cap:
> after every 5 completed tasks, write `progress.md` and remind the user that
> they can start a new session if responses start feeling truncated.

В `default.md` блок "Context Budget Awareness" переименовать в "Periodic Progress Snapshot" и привязать к счётчику тасков, а не к проценту контекста.

**Зависимость:** ничего, можно делать сразу.

**Время:** 15 минут.

---

## Block 2: Гейтинг ralph для TDD/worktree (≈1 час)

### 2.1 Детектор ralph

**Файл:** новый `skills/armchair-architect/lib/check_ralph.sh` (если решено добавить `lib/`),
либо inline в [steps/02_setup.md](../skills/armchair-architect/steps/02_setup.md).

**Что детектировать:**
1. Глобальный плагин: `ls ~/.claude/plugins/ralph-loop/SKILL.md 2>/dev/null`
2. Per-project плагин: `ls .claude/plugins/ralph-loop/SKILL.md 2>/dev/null`
3. Skill в стандартной локации: `ls ~/.claude/skills/ralph-loop/SKILL.md 2>/dev/null`
4. Включён в settings: `cat ~/.claude/settings.json | jq -e '.enabledPlugins["ralph-loop"]'`

Любого хита достаточно — выводить `installed`. Иначе `missing`.

### 2.2 Использовать в `02_setup.md`

В секции "TDD mode" (строки 54–69) перед вопросом про TDD сделать проверку.

**До:**
```
> **TDD mode** — each task follows: write failing tests → implement → verify green.
> Requires ralph-loop. Increases execution time, adds test coverage.
>
> Enable TDD? [y/n] *(default: n)*
```

**После:**
```bash
RALPH=$(... детектор ...)
```

```
If RALPH = "missing":
> **TDD mode** — requires ralph-loop, which is not installed.
> Skipping. To enable TDD later: install ralph-loop, then run
> `/armchair-architect use execute tdd`.
> Continuing with default executor.

If RALPH = "installed":
> **TDD mode** — each task: red → green → refactor. Enable? [y/n] (default: n)
```

### 2.3 Использовать в SKILL.md routing

В секции `### If arguments starts with "use "` ([SKILL.md:209-225](../skills/armchair-architect/skills/armchair-architect/SKILL.md)) перед записью `impl.execute = "tdd"` или `"worktree"` проверять ralph. Если missing — отказать:

> Cannot switch to **tdd** — ralph-loop not installed.
> Install: `git clone https://github.com/anthropics/ralph ~/.claude/plugins/ralph-loop`
> Then re-run `/armchair-architect use execute tdd`.

### 2.4 Verification

Создать два test fixture:
- `tests/fixtures/with_ralph/.claude/plugins/ralph-loop/SKILL.md` (пустой файл-маркер)
- `tests/fixtures/without_ralph/` (пусто)

Запустить детектор в обоих, проверить вывод.

**Время:** 1 час суммарно (детектор + 2 точки использования + fixtures).

---

## Block 3: Helper-библиотека и единый источник sequence (≈1 день)

Самый инвазивный блок. Делать после блоков 1 и 2 — чтобы не конфликтовать с правками заголовков.

**Зависимость:** требует дискуссии и переутверждения "no toolchain" decision в DESIGN.md и AGENTS.md.

### 3.1 Создать `lib/steps.json`

**Файл:** новый `skills/armchair-architect/lib/steps.json`

```json
[
  {"name": "init",            "file": "01_init.md",            "title": "Init & PRD Generation"},
  {"name": "setup",           "file": "02_setup.md",           "title": "Setup"},
  {"name": "interview_setup", "file": "03_interview_setup.md", "title": "Interview Setup"},
  {"name": "interview",       "file": "04_interview.md",       "title": "Interview"},
  {"name": "plan",            "file": "05_plan.md",            "title": "Strategy Plan"},
  {"name": "impl_plan",       "file": "06_impl_plan.md",       "title": "Implementation Plan & Tasks"},
  {"name": "execute",         "file": "07_execute.md",         "title": "Execute"}
]
```

### 3.2 Создать `lib/state.py`

**Файл:** новый `skills/armchair-architect/lib/state.py`

```python
"""State access layer for armchair-architect pipelines.
Used via: PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -c "from state import ..."
"""
import json, os, sys
from pathlib import Path

LIB_DIR = Path(__file__).parent

def _load_steps():
    with open(LIB_DIR / "steps.json") as f:
        return json.load(f)

STEPS = _load_steps()
STEP_NAMES = [s["name"] for s in STEPS]
STEP_FILE = {s["name"]: s["file"] for s in STEPS}

VALID_EXECUTE = ["default", "specialized", "ralph", "tdd", "worktree"]
VALID_CRITIQUE = ["none", "default", "strict"]
VALID_LANG = ["ru", "en"]

def active_pipeline():
    p = Path(".pipeline/active")
    return p.read_text().strip() if p.exists() else "default"

def state_path(name=None):
    return Path(f".pipeline/{name or active_pipeline()}/state.json")

def load():
    sp = state_path()
    if not sp.exists():
        return None
    with open(sp) as f:
        return json.load(f)

def save(s):
    sp = state_path()
    sp.parent.mkdir(parents=True, exist_ok=True)
    with open(sp, "w") as f:
        json.dump(s, f, indent=2)

def advance():
    s = load()
    cur = s["step"]
    s["completed"] = s.get("completed", []) + [cur]
    s["pending"] = [x for x in s.get("pending", []) if x != cur]
    s["step"] = s["pending"][0] if s["pending"] else "done"
    save(s)
    return s["step"]

def set_impl(component, value):
    s = load()
    s.setdefault("impl", {})[component] = value
    save(s)

def rollback_to(target):
    s = load()
    if target not in STEP_NAMES:
        raise ValueError(f"unknown step: {target}")
    target_idx = STEP_NAMES.index(target)
    to_rollback = [x for x in s.get("completed", []) if STEP_NAMES.index(x) >= target_idx]
    s["completed"] = [x for x in s.get("completed", []) if x not in to_rollback]
    s["pending"] = to_rollback + s.get("pending", [])
    s["step"] = target
    save(s)

def validate():
    """Returns list of error strings; empty list = ok."""
    s = load()
    if s is None:
        return []
    errors = []
    if s.get("step") not in STEP_NAMES + ["done"]:
        errors.append(f"unknown step: {s.get('step')!r}")
    pending, completed = s.get("pending", []), s.get("completed", [])
    overlap = set(pending) & set(completed)
    if overlap:
        errors.append(f"steps in both pending and completed: {sorted(overlap)}")
    if s.get("step") != "done" and s.get("step") not in pending:
        errors.append(f"step {s.get('step')!r} not in pending")
    impl = s.get("impl", {})
    if impl.get("execute") and impl["execute"] not in VALID_EXECUTE:
        errors.append(f"unknown impl.execute: {impl['execute']!r}")
    if impl.get("critique") and impl["critique"] not in VALID_CRITIQUE:
        errors.append(f"unknown impl.critique: {impl['critique']!r}")
    if s.get("lang") and s["lang"] not in VALID_LANG:
        errors.append(f"unknown lang: {s['lang']!r}")
    return errors
```

### 3.3 Заменить inline-snippets на вызовы библиотеки

**Что менять везде:**

| Старое (inline python) | Новое |
|---|---|
| ~12 строк advance state | `python3 -c "import sys; sys.path.insert(0, '${CLAUDE_SKILL_DIR}/lib'); from state import advance; print(advance())"` |
| set_impl | `... from state import set_impl; set_impl('<component>', '<value>')` |
| validate | `... from state import validate; errs = validate(); print('STATE ERROR: ' + '; '.join(errs)) if errs else None` |
| rollback (escalation) | `... from state import rollback_to; rollback_to('<target>')` |

**Затронутые файлы:**
- `skills/armchair-architect/SKILL.md` — секции `back`, `skip`, `use`, validation, default routing
- Все `steps/*.md` — финальные блоки advance state
- `impl/execute/default.md` — escalation rollback (это уже правит баг 1.1 заодно)
- `steps/02_setup.md` — `set_impl` для critique/execute/review_every

### 3.4 SKILL.md: убрать VALID_STEPS hardcode

В секции validation ([SKILL.md:244-285](../skills/armchair-architect/skills/armchair-architect/SKILL.md))
удалить inline-валидатор, заменить на вызов `from state import validate`.

В routing table ([SKILL.md:298-306](../skills/armchair-architect/skills/armchair-architect/SKILL.md))
описать routing через данные `steps.json`:

```bash
STEP=$(cat .pipeline/$(cat .pipeline/active)/state.json | jq -r .step)
FILE=$(cat ${CLAUDE_SKILL_DIR}/lib/steps.json | jq -r ".[] | select(.name==\"$STEP\") | .file")
echo "${CLAUDE_SKILL_DIR}/steps/$FILE"
```

И инструкция: "Read the resolved path with the Read tool, then follow its instructions."

### 3.5 Verification

Прогнать pipeline на тестовом проекте от `init` до `execute`. Проверить что все state-операции работают.

Запустить unit-тесты `state.py` (см. блок 5).

### 3.6 Обновить AGENTS.md и DESIGN.md

В AGENTS.md секцию "No build step, no dependencies" дополнить:
> Stdlib Python helpers in `lib/` are allowed. They are not a build step or external
> dependency — just shared code that prevents drift across 15+ inline snippets.
> Do not add packages requiring `pip install`.

В DESIGN.md в "Closed Design Decisions" добавить строку:
| State access via `lib/state.py` | All state mutations go through one helper module | Eliminates drift between 15+ inline snippets and centralizes step sequence |

**Время:** 1 день (helper + замены + тесты + документация).

---

## Block 4: Разбить `default.md` на под-файлы (≈4 часа)

**Зависимость:** делать после блока 3 — иначе будем дублировать inline-snippets в каждом под-файле.

### 4.1 Структура

```
impl/execute/
  default.md            ← главный loop, ~120 строк
  specialized.md        ← без изменений по сути
  ralph.md              ← без изменений
  tdd.md                ← без изменений
  worktree.md           ← без изменений
  _lib/
    parallel.md         ← parallel group dispatch + merge
    stuck.md            ← stuck task handling (4 опции)
    escalation.md       ← rollback to plan/impl_plan
    review_gate.md      ← code review subagent gate
    handoff.md          ← progress.md snapshot
    recovery.md         ← in_progress detection on restart
```

### 4.2 Что в `default.md` остаётся

```markdown
# Impl: Embedded Executor (default)

## Overview
[как сейчас]

## Response discipline
[как сейчас]

## Execution Loop

### Step A: Recovery check
On entry, check for interrupted tasks. See `${CLAUDE_SKILL_DIR}/impl/execute/_lib/recovery.md`.

### Step B: Find ready tasks
[короткая логика — определить ready set]

### Step C: Dispatch
- Sequential default — implement, verify, mark
- Parallel group detected — see `${CLAUDE_SKILL_DIR}/impl/execute/_lib/parallel.md`

### Step D: Per-task implement & verify
[короткая логика — 2 attempts, mark passes]

### Step E: Post-task gates
- If task stuck — see `${CLAUDE_SKILL_DIR}/impl/execute/_lib/stuck.md`
- If review_every triggered — see `${CLAUDE_SKILL_DIR}/impl/execute/_lib/review_gate.md`
- Periodic progress snapshot — see `${CLAUDE_SKILL_DIR}/impl/execute/_lib/handoff.md`

### Step F: Loop or stop
[как сейчас]

## Mid-run Stop
[как сейчас]

## Completion
[как сейчас]
```

### 4.3 Каждый под-файл

Самодостаточный — содержит и логику, и вызовы state.py. Никаких ссылок наружу кроме `default.md`.

### 4.4 specialized.md

Текущий [specialized.md](../skills/armchair-architect/impl/execute/specialized.md) уже грамотно делегирует в `default.md`. После разбиения он продолжит работать — переопределяет только Step C (parallel dispatch). Уточнить ссылку: "Override step C, see `_lib/parallel.md` — добавь role context из Role Map выше как первую строку prompt'а".

### 4.5 Verification

Прогнать execute на тестовом плане с:
- 3 sequential таска (default path)
- 1 parallel group из 2 тасков (parallel path)
- 1 интенсиально провальный таск (stuck path)

**Время:** 4 часа (выделение + перепроверка ссылок + smoke-тест).

---

## Block 5: Smoke-тесты state machine (≈1 день)

### 5.1 Структура

```
tests/
  README.md
  run_all.sh
  fixtures/
    state_clean.json          # свежая инициация
    state_mid_pipeline.json   # после interview
    state_corrupted.json      # invalid step name
    state_legacy.json         # для auto-migration
    state_overlap.json        # step в обоих completed/pending
  unit/
    test_state_load.sh
    test_state_validate.sh
    test_state_advance.sh
    test_state_rollback.sh
    test_state_set_impl.sh
  integration/
    test_routing_status.sh
    test_routing_back.sh
    test_routing_skip.sh
    test_routing_use.sh
    test_routing_pipelines.sh
    test_auto_migration.sh
```

### 5.2 Шаблон unit-теста

`tests/unit/test_state_advance.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
TESTS_DIR=$(dirname "$(realpath "$0")")/..
TMP=$(mktemp -d)
cd "$TMP"

mkdir -p .pipeline/default
cp "$TESTS_DIR/fixtures/state_mid_pipeline.json" .pipeline/default/state.json
echo default > .pipeline/active

PYTHONPATH="$TESTS_DIR/../skills/armchair-architect/lib" \
  python3 -c "from state import advance, load; advance(); s = load(); print(s['step'])" \
  > /tmp/out

EXPECTED="plan"
GOT=$(cat /tmp/out)
[ "$GOT" = "$EXPECTED" ] || { echo "FAIL: expected $EXPECTED, got $GOT"; exit 1; }
echo "PASS: test_state_advance"
```

### 5.3 Integration-тесты

Проверяют SKILL.md routing — но мы не можем запустить Claude Code из CI. Тогда integration-тесты проверяют поведение **shell-частей** SKILL.md (Python snippets, jq-фильтры). Идея:

1. Извлечь shell-блоки из SKILL.md по тегам:
   ```bash
   awk '/^### If arguments = "back"/,/^### If/' SKILL.md | grep -A 100 '```bash'
   ```
2. Запустить блок в подготовленном окружении.
3. Проверить итоговый state.json.

Это не покрывает решения LLM (что прочитать, что показать пользователю), но покрывает state machine — самую хрупкую часть.

### 5.4 GitHub Actions

`.github/workflows/test.yml`:
```yaml
name: smoke tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bash tests/run_all.sh
```

`tests/run_all.sh` — просто `for f in tests/{unit,integration}/*.sh; do bash "$f"; done`.

### 5.5 README.md тестов

Описать как добавлять новый тест, как локально запускать. Один раздел — "Что НЕ тестируется": LLM-поведение, шаблоны промптов.

**Время:** 1 день (структура + 5 unit + 5 integration + CI + docs).

---

## Block 6: Передача `CLAUDE.md` и interview answers в critique (≈1 час)

### 6.1 Default critique

**Файл:** [skills/armchair-architect/impl/critique/default.md](../skills/armchair-architect/impl/critique/default.md)

В секции PRD Critique перед запуском Agent:
```bash
CLAUDE_MD=""
[ -f CLAUDE.md ] && CLAUDE_MD=$(cat CLAUDE.md)
```

Изменить prompt:
```
Agent(prompt="You are a product/tech critic. Find problems in this PRD.

Project context (from CLAUDE.md, may be empty):
---
[insert $CLAUDE_MD]
---

PRD to critique:
---
[insert prd.md]
---

Look for: [как сейчас]")
```

В секции Implementation Plan Critique аналогично, плюс передавать `prd.md` целиком (не только `implementation_plan.md`):

```
Project context (CLAUDE.md):
---
[CLAUDE.md]
---

Approved PRD:
---
[prd.md]
---

Implementation plan to critique:
---
[implementation_plan.md]
---

Look for: [как сейчас]
```

### 6.2 Strict critique

В [strict.md](../skills/armchair-architect/impl/critique/strict.md) — то же самое, плюс ориентировка на стек из CLAUDE.md:

> If CLAUDE.md mentions specific runtime/framework, focus security and performance
> findings through that lens (e.g., for Node.js — async pitfalls, callback memory
> leaks; for Python — GIL implications; for PostgreSQL — connection pool sizing).

### 6.3 Verification

Запустить critique на тестовом PRD дважды:
- без CLAUDE.md
- с CLAUDE.md, явно описывающим Postgres + Python

Сравнить findings — second run должен содержать конкретные ссылки на стек.

**Время:** 1 час.

---

## Block 7: События в `events.jsonl` + `/stats` (≈4 часа)

### 7.1 Append helper в `lib/state.py`

```python
import time

def emit_event(event, **kwargs):
    """Append event to .pipeline/<active>/events.jsonl. Best-effort, never raises."""
    try:
        path = state_path().parent / "events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event}
        record.update(kwargs)
        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass
```

### 7.2 Точки эмиссии

Добавить вызовы `emit_event(...)`:

| Где | Событие |
|---|---|
| `default.md` после mark task pass | `task_pass`, args: `task_id`, `category`, `attempts` |
| `default.md` при stuck | `task_stuck`, args: `task_id`, `category`, `attempts`, `last_error` |
| `default.md` при escalation | `escalation`, args: `from_task`, `rolled_back_to` |
| `SKILL.md` команда `back` | `step_back`, args: `from`, `to` |
| `SKILL.md` команда `skip` | `step_skip`, args: `step` |
| `SKILL.md` команда `use` | `impl_change`, args: `component`, `from`, `to` |
| Каждый `advance()` | `step_complete`, args: `step` |

### 7.3 Команда `/armchair-architect stats`

Новая ветка в SKILL.md routing:

```
### If arguments = "stats"

Aggregate events from `.pipeline/<active>/events.jsonl`:
- Total tasks: N (passed: M, stuck: K)
- First-attempt pass rate: X%
- Stuck breakdown by category
- Step rollbacks: list
- Impl changes during this pipeline

Show as table.
```

Реализация — однострочный python:
```bash
python3 -c "
import json, collections
events = [json.loads(l) for l in open('.pipeline/$(cat .pipeline/active)/events.jsonl')]
counts = collections.Counter(e['event'] for e in events)
print(counts)
# ... агрегаты
"
```

### 7.4 events.jsonl в gitignore

Добавить в `.gitignore` пользовательских проектов (документировать в README, что наряду с `.pipeline/state.json` файл `events.jsonl` тоже игнорируется).

### 7.5 Verification

Прогнать минимальный pipeline (3 таска), убедиться что `events.jsonl` содержит ожидаемые записи. Запустить `/armchair-architect stats` — увидеть агрегаты.

**Время:** 4 часа.

---

## Block 8: Lite ↔ full sync (≈30 минут)

### 8.1 Документировать в AGENTS.md

Добавить раздел:
```
## Lite variant

`skills/armchair-architect-lite/SKILL.md` is a manually-maintained snapshot of the
full pipeline, condensed for single-session use without Claude Code.

When changing any of the following in full pipeline, update lite/SKILL.md to match:
- PRD template (`steps/01_init.md`)
- Plan structure (`steps/05_plan.md`)
- Implementation plan structure (`steps/06_impl_plan.md`)
- Per-task execution loop (`impl/execute/default.md` Step D)
- Stuck task split prompt
```

### 8.2 Чек-лист для PR

В `.github/pull_request_template.md`:
```
- [ ] If full pipeline templates changed — lite/SKILL.md updated to match
```

**Время:** 30 минут.

---

## Block 9: Закрытые decisions для пересмотра (≈2 часа)

### 9.1 Обсудить с автором

Не имплементировать в одиночку — это решения уровня дизайна:

1. **`specialized` vs `default` именование** — рекомендую переименовать `default.md` → `basic.md`,
   а `specialized.md` → `default.md`. Тогда state-значение `"default"` соответствует файлу
   `default.md`. Цена: миграция значения в существующих state.json пользователей.

2. **Critique opt-in → opt-out** — после стабилизации сделать дефолтным `default` (не `none`).
   Subagent latency приемлема для качества фидбэка.

3. **`lib/` директория** — подтвердить как закрытое design decision (см. Block 3.6).

### 9.2 Реализация после ack

- Переименование файлов через `git mv` + Edit ссылок в SKILL.md, AGENTS.md, DESIGN.md, README.md
- Auto-migration в SKILL.md: при чтении state, если `impl.execute == "default"` и файла `default.md` (нового) нет — это старое значение, заменить на `"basic"` и сохранить

**Время:** 2 часа после получения зелёного света.

---

## Очерёдность и зависимости

```
Block 1 (quick fixes)  ──┐
                          ├── Block 2 (ralph gating)
                          ├── Block 6 (critique context)
                          ├── Block 8 (lite docs)
                          │
                          └── Block 3 (lib/)  ──┬── Block 4 (split default.md)
                                                ├── Block 5 (tests)
                                                └── Block 7 (events + stats)
                                                       │
                                                       └── Block 9 (renames, after ack)
```

Параллельно (независимо): 1, 2, 6, 8.
После 3: 4, 5, 7.
После всего: 9.

Полная имплементация — ≈3-4 рабочих дня одному человеку.
Минимум для merge (блоки 1+2+6+8) — ≈3 часа.

---

## Что я могу сделать прямо сейчас

Без обсуждений и решений — блоки **1**, **2**, **6**, **8**. Это всё низко-инвазивные правки в существующих файлах.

Блоки **3** и далее требуют:
- Подтверждения "lib/ директория допустима" (нарушает текущее правило)
- Возможно дискуссии про переименование executors (block 9)

Если скажешь "делай блоки 1, 2, 6, 8" — могу пройтись прямо сейчас и сделать всё одной серией правок. Если "делай весь план" — начну с тех же блоков, потом подойду к блоку 3 и спрошу подтверждение перед изменением design rules.
