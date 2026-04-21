# План развития v1

Архитектурный ревью MVP + идеи для следующих итераций.

---

## Что работает хорошо

**Правильная проблема.** Главная боль LLM-кодогенерации — "прыгнул в код без контекста".
Pipeline заставляет пройти PRD → interview → plan → impl plan → tasks → execute. Реально снижает количество переделок.

**Двухуровневая абстракция (steps/ vs impl/).** Главное архитектурное решение в кодовой базе.
Разделение "что делать" (steps/) и "как делать" (impl/) позволяет:
- Заменить executor (ralph ↔ default) без изменения pipeline
- Подключить альтернативные режимы interview (MCP-based, form-based)
- Менять "как" не трогая контракт шагов

**Approval gates.** Gates на plan и impl_plan — ключевой момент. Без них LLM уходит в
реализацию по своему пониманию. Принудительная пауза для user review — это то, что
отличает полезный pipeline от опасного.

**Zero-dependency.** Никакого runtime кроме Claude Code. Чистый markdown.
Установка = git clone + одна строка в settings.json. Минимальный friction.

**Shell injection для state.** `` !`cat .pipeline/state.json 2>/dev/null || echo '{}'` ``
— элегантно. Нативный механизм Claude Code для инъекции живых данных в prompt.
Работает надёжно, не требует custom runtime.

**Default executor (встроенный).** Не зависеть от ralph — правильный default.
Progressive disclosure: работает из коробки, ralph — опция для продвинутых.

**Verification как shell commands.** `verification: ["npm test ...", "curl ..."]`
делает execution проверяемым. Exit code 0/non-0 — простой и надёжный контракт.

**Stuck task handling продуман.** 2 попытки → предложение split → user approval.
Не молча падает, не зацикливается, не меняет scope без спроса.

---

## Что хрупко

### 1. Линейность pipeline — главное ограничение

Жёсткая последовательность: init → interview → plan → impl_plan → tasks → execute.
На практике:
- После plan часто нужно вернуться к PRD (поняли что не то)
- После execute первых 3 тасков обнаруживается что plan надо менять
- Interview может быть не нужен вообще (пользователь пришёл с готовым PRD)

Единственный способ "вернуться" сейчас — reset и заново. Нет `goto`, нет `back`,
нет частичного отката. Для MVP окей, но это первое что начнёт мешать.

### 2. State management хрупкое

Каждый step файл хардкодит полный ожидаемый state JSON:
```json
{
  "step": "plan",
  "completed": ["init", "interview_setup", "interview"],
  "pending": ["plan", "impl_plan", "tasks", "execute"]
}
```
Добавить или убрать шаг → надо менять JSON во всех последующих step файлах.
Нет единого source of truth для списка шагов. SKILL.md содержит таблицу шагов,
но step файлы дублируют последовательность.

### 3. Один pipeline = один feature

Нет поддержки нескольких параллельных pipeline (например, feature A в execute,
feature B в interview). State — один файл `.pipeline/state.json`. Ограничит
при работе на больших проектах с несколькими фичами.

### 4. Нет валидации state

Ничто не проверяет что `state.json` консистентен. Ручное редактирование или
повреждение файла может поставить pipeline в невалидное состояние. LLM будет
пытаться интерпретировать мусор.

### 5. Context budget detection — приблизительный

"At ~40-50% estimated usage" — у Claude нет точного API для измерения использования
контекста. Будет работать как эвристика в лучшем случае. Особенно важно для
default executor, который работает в той же сессии.

### 6. Нет обратной связи от execution в planning

Если при выполнении тасков выясняется что архитектурный подход неверный,
pipeline не предусматривает "поднять проблему наверх" — только split stuck task.
Иногда нужно менять `plan.md`, а не дробить таску.

### 7. Interview — нет fast path

Один вопрос за раз — правильно для глубины, но для большого проекта: 20-30
вопросов × ожидание ответа. Нет fast path для опытных пользователей, которые
могут сразу дать технический контекст (дамп архитектуры, существующие ADR)
и пропустить interview.

### 8. `implementation_plan.json` — плоский список

Нет явных зависимостей между задачами (только implicit ordering). Если task 3.1
зависит от 2.3 — это нигде не выражено. Последовательное выполнение работает,
но нет поддержки переупорядочивания или параллелизации.

### 9. Интеграция с ralph — ручной handoff

"Скажи пользователю запустить /ralph-loop" — это инструкция, не интеграция.
Заметный friction: пользователь вручную переключается между двумя skills.

> **Статус:** не решается на нашей стороне — ждём skill-to-skill API от Claude Code.
> Убрано из активного backlog.

### 10. Шаги не идемпотентны

Если pipeline прервался в середине шага (network error, context overflow),
при повторном запуске `/armchair-architect` шаг начнётся заново с начала.
Для init/interview терпимо. Для execute — потенциальные конфликты от partial
code changes + restart.

### 11. Билингвальность — drift между фазами

`prd_ru.md`, `plan_ru.md`, `implementation_plan_ru.md` — теперь первичные документы для
русскоязычных пользователей. Английские версии (`prd.md` и т.д.) генерируются из
подтверждённых русских, а не наоборот. Для английских пользователей русских версий нет.

---

## Оценки

| Измерение | Оценка | Комментарий |
|---|---|---|
| Идея | 8/10 | Правильная проблема, правильный подход, хороший уровень абстракции |
| Техника | 7/10 | Сильно для zero-dependency markdown MVP; слабость в state management и линейности |

Главный риск: линейность pipeline начнёт мешать на реальных проектах.

---

## Новые возможности

### Context7 onboarding

Context7 — MCP-плагин с актуальной документацией библиотек. У автора включён глобально,
на новой машине может отсутствовать.

**Onboarding в `steps/01_init.md`:**

```
Проверь наличие context7:
!`cat ~/.claude/settings.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok' if d.get('enabledPlugins',{}).get('context7@claude-plugins-official') else 'missing')" 2>/dev/null || echo "missing"`
```

Если `missing` — предложить:
> Context7 не установлен. Это MCP-плагин с актуальной документацией библиотек —
> помогает писать корректный код для текущих версий зависимостей. Добавить? [y/n]

Если согласен: дописать `"context7@claude-plugins-official": true` в `enabledPlugins`
в `~/.claude/settings.json`. Нужен перезапуск сессии для активации.

**Использование в step файлах:**

`steps/05_impl_plan.md` — при декомпозиции на таски:
> Если доступен MCP context7 — используй его для актуальной документации зависимостей
> перед тем как описывать конкретные API вызовы в тасках.

`steps/07_execute.md` — перед выполнением таски:
> Если таска использует внешнюю библиотеку и доступен context7 — проверь актуальный API
> прежде чем писать код.

Принцип: мягкая рекомендация (`если доступен`), без hard dependency.

---

### Critic layer

Два subagent-критика в разных точках — чистый контекст, без истории генерации.

```
PRD → [КРИТИК → кормит interview] → interview → plan → impl_plan → [КРИТИК] → tasks → execute
```

**Критик PRD (после `01_init.md`)**

Самое ценное место: ошибка в требованиях расходится по всем фазам.

Что ловит: противоречия, неопределённый scope, пропущенные edge cases,
отсутствующие нефункциональные требования (auth, error handling, perf), неявные допущения о стеке.

Ключевой бонус: находки становятся стартовым списком вопросов для interview.
Результат сохраняется в `state.json` как `critique_prd`.

```
Agent(prompt="Ты product/tech critic. Найди проблемы в этом PRD:
[содержимое prd.md]
Ищи: противоречия, неопределённый scope, пропущенные edge cases,
отсутствующие нефункциональные требования, неявные допущения.
Выдай нумерованный список конкретных проблем. Без похвалы.")
```

**Критик impl_plan (после `05_impl_plan.md`)**

Детальный технический ревью перед нарезкой задач — дёшево исправить, до execute.

Что ловит: неправильный порядок шагов, пропущенные зависимости между блоками,
задачи слишком крупные для одного контекстного окна, неверные допущения о коде.

Результат показывается пользователю вместе с approval gate.

```
Agent(prompt="Ты senior engineer. Найди проблемы в этом implementation plan:
[содержимое implementation_plan.md]
Ищи: неправильный порядок, пропущенные шаги, слишком крупные задачи,
отсутствующие зависимости, неверные допущения о стеке.
Выдай нумерованный список конкретных проблем. Без похвалы.")
```

Критик после `plan.md` — не добавлять: низкий ROI, через шаг будет impl_plan критик.

**Impl/ вариации:**

| Impl | Поведение |
|---|---|
| `impl/critique/default.md` | Оба критика (PRD + impl_plan) |
| `impl/critique/strict.md` | Строже: security/perf угол, больше вопросов |
| `impl/critique/none.md` | Отключить (быстрые итерации) |

Включается: `/armchair-architect use critique strict`

---

### TDD gate

Опциональный шаг между `tasks` и `execute`. Пользователю задаётся вопрос:
> Использовать TDD режим? (тесты → реализация → рефактор для каждой задачи) [y/n]

Если да — `impl` переключается на `tdd`, state обновляется.

**Важно:** TDD executor — инъекция TDD протокола поверх ralph, не замена.
Дефолтный executor для TDD не подходит: к фазе execute контекст уже заполнен
interview/planning фазами. Ralph запускает каждую задачу в свежей сессии.

`impl/execute/tdd.md` = ralph.md + расширение каждой задачи:

```json
{
  "id": "task-03",
  "description": "...",
  "tdd": {
    "tests_first": "Напиши failing тесты прежде чем писать реализацию",
    "verify_red": "npm test -- --testPathPattern=task03 должен упасть",
    "verify_green": "npm test -- --testPathPattern=task03 должен пройти"
  }
}
```

Включается через: `/armchair-architect use execute tdd` (требует ralph-loop)

---

### Git worktrees executor

Новый `impl/execute/worktree.md`:
- Создаёт изолированный git worktree для feature branch перед execute
- Выполняет таски в нём, PR при успехе
- Ценность: нет риска загрязнить main branch частично выполненными тасками

---

### Параллельные subagents

Расширение схемы `implementation_plan.json`:
```json
{ "id": "task-03", "parallel": true, "group": "api-layer" }
```
Таски с одинаковым `group` + `parallel: true` → запускаются через Agent tool одновременно.
Реализуется в `impl/execute/` без изменения `steps/`.

---

### armchair-architect-lite

Новый skill `skills/armchair-architect-lite/SKILL.md` — один файл, без state machine.
Совместим с GitHub Copilot (`.github/skills/`) и Cursor.
Цель: 60–70% ценности через структурированный промпт без pipeline machinery.

Что теряется: state persistence, swappable impl/, ralph executor, enforcement gates.
Что сохраняется: PRD → interview → plan → impl → execute структура, chunked interview, языковые настройки.

---

### Прочие улучшения pipeline

**`/armchair-architect back`** — возврат на предыдущий шаг без полного reset.
Новый routing case в `SKILL.md`: pop последнего completed, push обратно в pending.

**Skip paths** — `/armchair-architect skip interview` / `skip planning`.
Routing в `SKILL.md`: проверить наличие файла-артефакта и перепрыгнуть шаг.

**Context handoff** — авто-детект ~40% контекста (эвристика): пишет `progress.md`,
предлагает начать новую сессию.

**Ralphex executor** — `impl/execute/ralphex.md`; placeholder до стабилизации API.

**Code review gate** — каждые N тасков в execute impl: pause и review pass.
Настраивается через state.json.

---

## Приоритеты

### P1 — Быстрые wins (низкая сложность, высокий impact)

1. ✅ **`back` команда** — новый routing case в SKILL.md
2. ✅ **Skip paths** — `skip interview` / `skip planning` в SKILL.md
3. ✅ **Context7 onboarding** — проверка + предложение установить в `02_setup.md`; рекомендация в `06_impl_plan.md` и `07_execute.md`

### P2 — Архитектурные улучшения

4. ✅ **Централизованный реестр шагов** — убрать хардкод state JSON из каждого step файла
5. ✅ **Critic layer** — `impl/critique/`: два subagent-критика (PRD + impl_plan)
6. ✅ **armchair-architect-lite** — для Copilot/Cursor
7. ✅ **TDD gate executor** — `impl/execute/tdd.md` поверх ralph
8. ✅ **Git worktrees executor** — `impl/execute/worktree.md`

### Дополнительно реализовано (вне оригинального плана)

- ✅ **`list` команда** — список доступных impl вариантов
- ✅ **`setup` шаг (02_setup.md)** — context7, critique mode, TDD mode в одном месте
- ✅ **Билингвальный порядок** — `prd_ru.md` первичен для ru, `prd.md` выводится из него
- ✅ **Слияние impl_plan + tasks** — JSON генерируется сразу после одобрения markdown

### P3 — Сложные / отложенные

9. ✅ **Параллельные subagents** — `parallel`/`group` в JSON схеме + Agent tool в executor
9б. **Специализированные агенты** — при параллельном запуске выбирать промпт по `category` задачи (backend/frontend/database). Новый `impl/execute/specialized.md` поверх parallel executor. Не требует изменений в `steps/`.
10. **Multi-pipeline support** — `.pipeline/<feature>/state.json`
11. ✅ **Context handoff** — авто-детект ~40% контекста, запись progress.md
12. ✅ **Code review gate** — pause каждые N тасков в execute
13. **Interview fast path** — принять дамп документов, пропустить к подтверждению
14. ✅ **Escalation execution → planning** — "эта таска выявила проблему уровня плана"
15. ✅ **Зависимости в JSON схеме** — явное поле `dependsOn`
16. ✅ **Валидация state** — базовая проверка схемы при загрузке
17. **Идемпотентность шагов** — корректная обработка прерванных шагов в execute
18. **Ralphex executor** — `impl/execute/ralphex.md`; ждём стабилизации API

---

## Что не трогать

- Shell injection для state (`!` preprocessing) — работает, не менять
- Двухуровневая абстракция steps/impl — главное архитектурное достоинство, не схлопывать
- Approval gates на plan и impl_plan — не подлежит изменению
- Zero-dependency философия — никаких build steps, никакого внешнего runtime
