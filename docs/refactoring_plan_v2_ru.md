# План развития v2

Ревью feature/refactoring-v1 + направления для v2.

Контекст: v1 закрыл большую часть пунктов из [refactoring_plan_v1_ru.md](./refactoring_plan_v1_ru.md)
(линейность, multi-pipeline, валидация state, interrupt recovery). Этот документ — про то,
что осталось и что вылезло нового после рефакторинга.

---

## Что v1 закрыл

| Пункт из v1 | Статус | Где |
|---|---|---|
| 1. Линейность pipeline | ✅ закрыто | `back`, `skip interview/planning`, escalation rollback |
| 2. State management хрупкое | 🟡 частично | валидация добавлена, но sequence всё ещё дублируется в 3 местах |
| 3. Один pipeline = одна фича | ✅ закрыто | `.pipeline/active` + `<feature>/state.json` |
| 4. Нет валидации state | ✅ закрыто | `VALID_STEPS`/`VALID_EXECUTE`/`VALID_CRITIQUE` в SKILL.md |
| 5. Context budget detection приблизительный | 🔴 не закрыто | по-прежнему "~40-50% estimated usage" |

Дополнительно появилось то, чего в v1 не планировалось:
- **`armchair-architect-lite`** — однофайловая версия для Copilot/Cursor
- **Critique mode** (none/default/strict) — subagent-критики на PRD и impl plan
- **Specialized executor** — role-aware subagents в parallel dispatch
- **Параллелизм** — `parallel`/`group` в JSON, мердж результатов через temp-файлы
- **Code review gate** — каждые N тасков subagent ревьюит `git diff`
- **Bilingual sync** — RU primary, EN derived автоматически на phase boundaries

---

## Что осталось хрупким после v1

### 1. Inline Python везде — главный источник багов

Паттерн `python3 -c "..."` повторяется 15+ раз: в [SKILL.md](../skills/armchair-architect/SKILL.md),
во всех `steps/NN_*.md`, в [impl/execute/default.md](../skills/armchair-architect/impl/execute/default.md).
Каждый раз дублируется блок чтения active pipeline:

```python
import os as _os
_active = open('.pipeline/active').read().strip() if _os.path.exists('.pipeline/active') else 'default'
_sp = f'.pipeline/{_active}/state.json'
```

**Конкретный баг уже есть:** в [impl/execute/default.md:303-313](../skills/armchair-architect/impl/execute/default.md)
блок escalation rollback сломан по отступам — после `_active = ... _sp = ...` идёт
`with open(_sp) as f: s = json.load(f)` без отступа от внутреннего `python3 -c`.
В реальном запуске будет `IndentationError`.

**Почему опасно:**
- Hard to lint — Python спрятан в строках
- Hard to test — нельзя запустить отдельно
- Drift — если сменить state schema, надо найти все 15+ snippet'ов вручную
- AGENTS.md требует "no toolchain" — нельзя добавить shared `lib.py`

**Направление имплементации:**
- **A.** Внести единый helper `${CLAUDE_SKILL_DIR}/lib/state.py` с функциями
  `load_state()`, `save_state(s)`, `advance_step()`, `set_impl(component, value)`.
  Шаги вызывают через `python3 -c "from state import advance_step; advance_step()"`
  (через `PYTHONPATH=${CLAUDE_SKILL_DIR}/lib`). Это **нарушает** "no toolchain", но
  пакетов добавлять не надо — только один py-файл. Стоит обсудить как закрытое
  design decision.
- **B.** Если строго без shared кода — генерировать step-файлы из шаблона и держать
  snippets в одном месте. Но это вводит build step, что хуже.
- **C.** Минимум: вынести inline-snippets в bash-вызовы вида
  `bash ${CLAUDE_SKILL_DIR}/lib/advance.sh <step>`. Меньше escapings, легче читать.

Рекомендую **A** — `lib/` директория как часть skill-а это не toolchain, это просто
организация кода. В DESIGN.md задокументировать как "data-access layer".

---

### 2. Sequence шагов дублируется в 3 местах

Список шагов pipeline хардкоден в:

1. **Routing table** в [SKILL.md:298-306](../skills/armchair-architect/skills/armchair-architect/SKILL.md):
   ```
   | init | steps/01_init.md |
   | setup | steps/02_setup.md |
   ...
   ```
2. **`VALID_STEPS`** в валидаторе ([SKILL.md:247](../skills/armchair-architect/SKILL.md)):
   ```python
   VALID_STEPS = ['init','setup','interview_setup','interview','plan','impl_plan','execute','done']
   ```
3. **`all_steps`** в escalation rollback ([impl/execute/default.md:307](../skills/armchair-architect/impl/execute/default.md)):
   ```python
   all_steps = ['init','setup','interview_setup','interview','plan','impl_plan','execute']
   ```

Любое переименование/добавление шага требует синхронных правок во всех трёх местах.
Refactoring plan v1 это уже флагал — после рефакторинга проблема не ушла, а размножилась
(было 7 мест в step-файлах, стало 3 source-of-truth).

**Направление имплементации:**
- Источник истины — `${CLAUDE_SKILL_DIR}/lib/steps.json`:
  ```json
  [
    {"name": "init", "file": "01_init.md"},
    {"name": "setup", "file": "02_setup.md"},
    ...
  ]
  ```
- SKILL.md читает через shell injection: `!`cat ${CLAUDE_SKILL_DIR}/lib/steps.json``
- Валидатор и escalation подгружают тот же файл
- Если в результате решено держать helper из пункта 1 — `steps.json` логично положить рядом

---

### 3. Off-by-one в нумерации после рефакторинга

[steps/06_impl_plan.md](../skills/armchair-architect/steps/06_impl_plan.md) — артефакты
переименования:

- Заголовок: `# Step 05 — Implementation Plan & Tasks` (должно быть `Step 06`)
- Нумерация секций прыгает: `### 8. Generate implementation_plan.json` → `### 10. Show summary` (нет `### 9`)

Не критично, но снижает доверие. Для prompt-based проекта аккуратность markdown это часть API.

**Направление имплементации:** простая правка. Заодно пройтись `grep -rn "Step 0" skills/`
и проверить остальные шаги.

---

### 4. Скрытые зависимости от ralph

В [steps/02_setup.md:54-69](../skills/armchair-architect/steps/02_setup.md) пользователю
предлагается включить TDD. Если он соглашается — `impl.execute = "tdd"`. Но проверки,
что ralph установлен, нет. Юзер увидит ошибку только в `execute` шаге, на этапе когда
уже потратил время на interview/plan/impl_plan.

То же касается `worktree` executor — он tells user `/ralph-loop` без проверки.

**Направление имплементации:**
- В `02_setup.md` детектить ralph через `ls ~/.claude/plugins/ralph-loop` или
  `cat ~/.claude/settings.json | jq '.enabledPlugins["ralph-loop"]'`
- Если нет — TDD/worktree варианты помечать как `(unavailable, install ralph-loop first)`
  и блокировать выбор
- Аналогично для `use execute tdd` — отказывать с понятным сообщением

---

### 5. `default.md` слишком большой (402 строки)

[impl/execute/default.md](../skills/armchair-architect/impl/execute/default.md) тянет:
- Sequential execution loop
- Parallel group dispatch
- Stuck task handling (4 опции)
- Escalation rollback с rewriting state
- Code review gate
- Context handoff (`progress.md`)
- Interrupt recovery (`in_progress` флаг)
- Completion

Каждый сценарий разбавляет основной loop. Для LLM это значит: чем длиннее prompt, тем
выше шанс что часть инструкций будет проигнорирована.

**Направление имплементации:**
- Разбить на под-файлы которые `default.md` подгружает по необходимости:
  - `impl/execute/_lib/parallel.md`
  - `impl/execute/_lib/stuck.md`
  - `impl/execute/_lib/escalation.md`
  - `impl/execute/_lib/review_gate.md`
  - `impl/execute/_lib/handoff.md`
- В `default.md` остаётся только основной loop + ссылки "Если задача застряла —
  следуй `${CLAUDE_SKILL_DIR}/impl/execute/_lib/stuck.md`"
- `specialized.md` так же ссылается на эти под-файлы, не дублируя

---

### 6. Lite дублирует ~50% контента full

[armchair-architect-lite/SKILL.md](../skills/armchair-architect-lite/SKILL.md) содержит
свои PRD-шаблон, plan-шаблон, impl-plan-шаблон, executor loop. При любом изменении
шаблонов в full-версии lite будет дрейфовать.

**Направление имплементации:**

Варианты по убыванию инвазивности:
- **A.** Принять дрейф и явно задокументировать в AGENTS.md, что lite — снапшот full-а,
  обновляется вручную при значимых изменениях. Простейший вариант.
- **B.** Вынести шаблоны (PRD structure, plan structure, impl plan structure) в
  `lib/templates/` и подгружать в обоих через `cat ${CLAUDE_SKILL_DIR}/...`. Но lite
  по дизайну должен работать **без** Claude Code (Copilot/Cursor) — там нет
  `${CLAUDE_SKILL_DIR}` и shell injection. Не подходит для lite.
- **C.** Build step: `make lite` собирает `lite/SKILL.md` из шаблонов. Нарушает
  "no toolchain", но один Makefile это копеечная цена за устранение дрейфа.

Рекомендую **A** — задокументировать pairing и проходить чек-лист при изменениях
("если меняешь PRD-шаблон в `01_init.md` — обнови в lite/SKILL.md тоже").

---

### 7. Critique получает мало контекста

[impl/critique/default.md:13-26](../skills/armchair-architect/impl/critique/default.md)
запускает subagent с PRD и общими инструкциями ("be direct, no praise"). Но не передаёт:
- Содержимое `CLAUDE.md` (стек, conventions, что не трогать)
- Кто целевой пользователь, какой проект (личный/корпоративный/OSS)
- Контекст ответов из interview (для impl plan critique)

Critic выдаёт generic фидбэк про "missing edge cases" вместо конкретики типа
"в этом проекте уже используется PostgreSQL — указать диалект явно".

**Направление имплементации:**
- В critique-promise добавить блок:
  ```
  Project context (CLAUDE.md):
  ---
  [insert CLAUDE.md contents if present]
  ---
  ```
- Для impl plan critique — также передавать `prd.md` и список ответов из interview
  (если хранятся в state)
- Strict mode критиковать ещё и через призму конкретного стека
  (например, для Python — concurrency model, для Go — error handling)

---

### 8. Context budget detection всё ещё guess

`At ~40-50% estimated usage` — Claude не выдаёт точную цифру. На практике LLM либо
никогда не сработает (продолжит до hard limit), либо сработает слишком рано.

Refactoring plan v1 это флагал. В v1 ничего не изменилось.

**Направление имплементации:**
- Honest fallback: писать `progress.md` каждые N тасков (например N=5), а не по budget.
  Тогда `progress.md` всегда актуален, даже если context уехал в hard limit.
- Опционально: показывать пользователю "completed M tasks, recommend new session
  every K tasks" — пусть он сам вызывает `/clear`.
- Удалить misleading "~40-50%" из step-файлов и documentation.

---

### 9. Нет smoke-тестов

Иронично для проекта, который сам форсит `verification: [...]` для каждого таска.

Минимум что хочется протестировать:
- SKILL.md routing для каждой команды (`status`, `reset`, `back`, `skip`, `pipelines`,
  `new`, `switch`, `list`, `use`)
- State validation отлавливает unknown step / unknown impl / overlapping completed+pending
- Auto-migration legacy state → `default/`
- `back` корректно перекидывает шаги между completed/pending
- escalation rollback в plan возвращает execute, impl_plan, plan в pending

**Направление имплементации:**
- `tests/` директория с bash-скриптами:
  ```
  tests/
    fixtures/
      state_clean.json
      state_legacy.json
      state_corrupted.json
    test_routing.sh
    test_validation.sh
    test_back.sh
  ```
- Каждый тест: подставляет fixture, симулирует ввод (echo в stdin), проверяет
  diff state.json до/после
- CI: GitHub Actions, `bash tests/run_all.sh`. Никаких npm/pip — только bash.
- Тесты не проверяют LLM поведение (это невозможно без real API), только
  детерминированные части: state machine, routing, валидация.

---

### 10. Нет метрик/телеметрии

Сейчас нельзя понять:
- Сколько тасков проходят verification с первого раза
- Какие категории тасков чаще застревают (backend? frontend? infra?)
- Как часто пользователь использует `back` / escalation
- Реальное распределение времени execute vs interview vs plan

Это нужно для tuning'а самого pipeline (например, обнаружить что `frontend` таски
застревают в 60% случаев и пересмотреть `specialized.md` role context).

**Направление имплементации:**
- Append-only `.pipeline/<feature>/events.jsonl`:
  ```json
  {"ts": "2026-04-22T10:30:00Z", "event": "task_pass", "task_id": "1.1", "category": "backend", "attempts": 1}
  {"ts": "2026-04-22T10:35:00Z", "event": "task_stuck", "task_id": "1.2", "category": "frontend", "attempts": 2}
  {"ts": "2026-04-22T10:40:00Z", "event": "step_back", "from": "execute", "to": "impl_plan"}
  ```
- Команда `/armchair-architect stats` — простой агрегат по `events.jsonl`
- Опционально: команда `/armchair-architect report` — markdown-отчёт по фиче
  (для PR description / постмортема)
- Никакой телеметрии наружу. Файл в `.gitignore` рядом с `state.json`.

---

## Что хочется добавить (новые направления)

### A. Интеграция с трекерами

`implementation_plan.json` живёт в репо, но реальная работа отслеживается в Linear/Jira/
GitHub Issues. Хотелось бы:
- `/armchair-architect export github` — создать GitHub issue на каждый таск
- `/armchair-architect sync github` — обновить статусы issue по `passes: true/false`

**Имплементация:** опциональный impl variant `impl/tracker/{none,github,linear}.md`.
По дефолту `none` — текущее поведение. github работает через `gh issue create/edit` —
не требует custom auth.

### B. Демо/скринкаст

README обещает многое, но нет визуала. Для adoption критично. 2-минутный asciinema/loom:
"описываю проект → PRD → 3 вопроса → план → execute 3 таска". Один раз сделать —
сильно упростит pitch.

### C. `/armchair-architect diff <step>`

Показать что изменилось с момента последнего вызова шага. Например, после `back interview`
и повторного `interview` — увидеть diff `prd.md` до/после. Сейчас такой возможности нет,
а это важно для понимания что критика интервью реально дала.

**Имплементация:** перед каждым шагом, который меняет файлы — снапшот в
`.pipeline/<feature>/snapshots/<step>_<timestamp>.tar`. Команда `diff` сравнивает
последние два.

### D. Парная работа critique + interview

Сейчас critique запускается в `01_init.md` после генерации PRD, и его выводы (`critique_prd`)
становятся входом для interview. Но в interview эти findings нигде явно не используются
в [04_interview.md](../skills/armchair-architect/steps/04_interview.md) — только как
"starting input". Стоит явно прописать: "первые N вопросов адресуют `critique_prd`".

### E. Skill-to-skill API когда появится

В [DESIGN.md:262](../DESIGN.md) deferred. Когда Claude Code добавит skill invocation —
ralph можно будет звать напрямую без "tell user to run `/ralph-loop`". Это уберёт самый
неуклюжий момент в worktree/tdd executors.

---

## Приоритеты

Если делать всё сразу — нереально. Предлагаемая очерёдность:

| # | Что | Почему первым | Усилия |
|---|---|---|---|
| 1 | Фикс отступов в `default.md:303-313` | Реальный баг, blocker для escalation flow | 5 мин |
| 2 | Off-by-one в `06_impl_plan.md` | Тривиально, повышает доверие | 10 мин |
| 3 | Гейтинг ralph для TDD/worktree в `02_setup.md` | UX bug — фрустрация после долгого pipeline | 1 час |
| 4 | Honest fallback для context handoff (5 тасков) | Удаляет ложную фичу | 30 мин |
| 5 | Smoke-тесты state machine + CI | Окупится при следующей правке SKILL.md | 1 день |
| 6 | Helper-библиотека (`lib/state.py`) + единый `steps.json` | Закрывает пункты 1 и 2 разом | 1 день |
| 7 | Разбить `default.md` на под-файлы | Делать после п.6 — тогда state-операции уже в библиотеке | 0.5 дня |
| 8 | Передавать `CLAUDE.md` в critique | Качество фидбэка вырастет заметно | 1 час |
| 9 | События в `events.jsonl` + `/stats` | Foundation для tuning'а | 0.5 дня |
| 10 | Демо | Adoption | 2 часа на запись + редактирование |

Остальное (трекеры, diff, парность critique+interview) — после.

---

## Закрытые design decisions, которые стоит пересмотреть

| Решение | Где | Почему пересмотреть |
|---|---|---|
| "No toolchain" | AGENTS.md | Inline Python уже создаёт техдолг. Один helper-файл это не toolchain. |
| "Specialized как default" | DESIGN.md:235 | Назначение `specialized` дефолтом, при наличии файла `default.md`, путает. Стоит переименовать `default.md` → `basic.md` либо `specialized.md` → `default.md` (с переименованием значения в state). |
| "Critique opt-in (none default)" | DESIGN.md:232 | После рефакторинга critique стал стабильнее. Возможно пора сделать дефолтом `default` (не `strict`). Subagent latency — приемлемая цена за качество. |

---

## Что НЕ менять

Не сломайте то, что работает:

- Двухуровневую абстракцию `steps/` vs `impl/` — это причина, по которой v1 удалось
  без боли расширить (3 новых executors, 3 critique варианта)
- Подход RU-primary / EN-derived — единственный способ избежать translation drift
- Approval gates на plan и impl_plan — без них pipeline теряет смысл
- `parallel: true` + `group` через temp-файлы — конкурентная запись в один JSON
  была бы кошмаром, текущее решение надёжное
- Markdown-only / zero runtime — главный USP проекта, не растерять
