"""State access layer for armchair-architect pipelines.

Single source of truth for state.json reads/writes, step sequence, and validation.
Replaces ~15 inline `python3 -c "..."` snippets that previously duplicated this logic
across SKILL.md, steps/*.md, and impl/execute/default.md.

Usage from a markdown prompt:
    PYTHONPATH=${CLAUDE_SKILL_DIR}/lib python3 -c "from state import advance; advance()"

Usage from a CLI for tests:
    PYTHONPATH=skills/armchair-architect/lib python3 -m state validate
"""
import json
import os
import sys
import time
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent


def _load_steps():
    with open(LIB_DIR / "steps.json") as f:
        return json.load(f)


STEPS = _load_steps()
STEP_NAMES = [s["name"] for s in STEPS]
STEP_FILE = {s["name"]: s["file"] for s in STEPS}

VALID_EXECUTE = ["default", "basic", "ralph", "tdd", "worktree"]
VALID_CRITIQUE = ["none", "default", "strict"]
VALID_LANG = ["ru", "en"]

# Old impl.execute names → new names. Applied by auto_migrate_legacy().
# `specialized` was renamed to `default` (the role-aware executor is now the recommended default).
# Note: the old `default` (basic embedded executor) is now `basic.md`, but we cannot auto-migrate
# `"execute": "default"` because that value is still valid (with new semantics) — any old pipeline
# that explicitly chose the basic executor must be updated manually with `use execute basic`.
EXECUTE_RENAMES = {"specialized": "default"}


# ---------- paths ----------

def active_pipeline():
    p = Path(".pipeline/active")
    return p.read_text().strip() if p.exists() else "default"


def state_path(name=None):
    return Path(f".pipeline/{name or active_pipeline()}/state.json")


# ---------- I/O ----------

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


# ---------- mutations ----------

def advance():
    """Advance state: move current step from pending to completed, set step to next pending."""
    s = load()
    if s is None:
        return None
    cur = s.get("step")
    s["completed"] = s.get("completed", []) + [cur]
    s["pending"] = [x for x in s.get("pending", []) if x != cur]
    s["step"] = s["pending"][0] if s["pending"] else "done"
    save(s)
    return s["step"]


def set_impl(component, value):
    s = load() or {}
    s.setdefault("impl", {})[component] = value
    save(s)


def set_lang(lang):
    s = load() or {}
    s["lang"] = lang
    save(s)


def rollback_one():
    """`back` command: pop last completed step, prepend to pending, set as current step."""
    s = load()
    if s is None or not s.get("completed"):
        return None
    prev = s["completed"].pop()
    s["pending"] = [prev] + s.get("pending", [])
    s["step"] = prev
    save(s)
    return prev


def rollback_to(target):
    """Escalation: roll back to `target` step. All steps after target move from completed to pending."""
    if target not in STEP_NAMES:
        raise ValueError(f"unknown step: {target!r}")
    s = load()
    if s is None:
        return None
    target_idx = STEP_NAMES.index(target)
    to_rollback = [x for x in s.get("completed", []) if STEP_NAMES.index(x) >= target_idx]
    s["completed"] = [x for x in s.get("completed", []) if x not in to_rollback]
    s["pending"] = to_rollback + s.get("pending", [])
    s["step"] = target
    save(s)
    return target


def skip_to_after(steps_to_skip):
    """`skip` command: mark each step in steps_to_skip as completed (if pending)."""
    s = load()
    if s is None:
        return None
    pending = s.get("pending", [])
    completed = s.get("completed", [])
    for st in steps_to_skip:
        if st in pending:
            pending.remove(st)
        if st not in completed:
            completed.append(st)
    s["pending"] = pending
    s["completed"] = completed
    s["step"] = pending[0] if pending else "done"
    save(s)
    return s["step"]


# ---------- validation ----------

def validate():
    """Returns list of error strings. Empty list = state is valid (or absent)."""
    s = load()
    if s is None:
        return []
    errors = []
    step = s.get("step")
    if step not in STEP_NAMES + ["done"]:
        errors.append(f"unknown step: {step!r}")
    pending = s.get("pending", [])
    completed = s.get("completed", [])
    if not isinstance(pending, list):
        errors.append("pending is not a list")
    if not isinstance(completed, list):
        errors.append("completed is not a list")
    if isinstance(pending, list) and isinstance(completed, list):
        overlap = set(pending) & set(completed)
        if overlap:
            errors.append(f"steps in both pending and completed: {sorted(overlap)}")
        if step != "done" and step not in pending:
            errors.append(f"step {step!r} not in pending")
    lang = s.get("lang")
    if lang and lang not in VALID_LANG:
        errors.append(f"unknown lang: {lang!r}")
    impl = s.get("impl", {})
    exe = impl.get("execute")
    if exe and exe not in VALID_EXECUTE:
        errors.append(f"unknown impl.execute: {exe!r}")
    crit = impl.get("critique")
    if crit and crit not in VALID_CRITIQUE:
        errors.append(f"unknown impl.critique: {crit!r}")
    return errors


# ---------- migration ----------

def initial_state():
    """Default state for a freshly-created pipeline."""
    return {
        "step": STEP_NAMES[0],
        "completed": [],
        "pending": list(STEP_NAMES),
        "impl": {"interview": "ask_user_question", "execute": "default", "critique": "none"},
    }


def auto_migrate_legacy():
    """Run all idempotent migrations on the active pipeline. Returns True if anything changed."""
    changed = False

    # 1) Single-pipeline -> multi-pipeline layout (move .pipeline/state.json -> .pipeline/default/state.json)
    legacy = Path(".pipeline/state.json")
    active = Path(".pipeline/active")
    if legacy.exists() and not active.exists():
        target_dir = Path(".pipeline/default")
        target_dir.mkdir(parents=True, exist_ok=True)
        legacy.rename(target_dir / "state.json")
        active.write_text("default")
        changed = True

    # 2) Bootstrap: if no state file exists for the active pipeline, create one with defaults.
    # This makes first-run safe — without it, validate() returns ok (state is None), then
    # subsequent `state load` prints "null" and downstream JSON parsers crash.
    if not active.exists():
        active.parent.mkdir(parents=True, exist_ok=True)
        active.write_text("default")
        changed = True
    sp = state_path()
    if not sp.exists():
        save(initial_state())
        changed = True

    # 3) Rename old impl.execute values (e.g., "specialized" -> "default")
    s = load()
    if s is not None:
        impl = s.get("impl", {})
        old = impl.get("execute")
        if old in EXECUTE_RENAMES:
            impl["execute"] = EXECUTE_RENAMES[old]
            s["impl"] = impl
            save(s)
            changed = True

    return changed


# ---------- pipelines (multi-pipeline support) ----------

def list_pipelines():
    """Returns list of (name, step, is_active) tuples."""
    base = Path(".pipeline")
    if not base.exists():
        return []
    active = active_pipeline()
    out = []
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        sp = d / "state.json"
        if not sp.exists():
            continue
        with open(sp) as f:
            step = json.load(f).get("step", "?")
        out.append((d.name, step, d.name == active))
    return out


def create_pipeline(name):
    Path(f".pipeline/{name}").mkdir(parents=True, exist_ok=True)
    Path(".pipeline/active").write_text(name)


def switch_pipeline(name):
    if not Path(f".pipeline/{name}/state.json").exists():
        return False
    Path(".pipeline/active").write_text(name)
    return True


def reset_active():
    sp = state_path()
    if sp.exists():
        sp.unlink()


# ---------- events ----------

def emit_event(event, **kwargs):
    """Append event to .pipeline/<active>/events.jsonl. Best-effort, never raises."""
    try:
        path = state_path().parent / "events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
        }
        record.update(kwargs)
        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def read_events():
    """Returns list of event dicts from events.jsonl, or [] if missing."""
    path = state_path().parent / "events.jsonl"
    if not path.exists():
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


# ---------- CLI for tests ----------

def _cli():
    if len(sys.argv) < 2:
        print("usage: python3 -m state <command> [args]", file=sys.stderr)
        sys.exit(2)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == "validate":
        errs = validate()
        if errs:
            print("STATE ERROR: " + "; ".join(errs))
            sys.exit(1)
        print("ok")
    elif cmd == "advance":
        print(advance() or "")
    elif cmd == "rollback-one":
        print(rollback_one() or "NOTHING_TO_ROLLBACK")
    elif cmd == "rollback-to":
        print(rollback_to(args[0]) or "")
    elif cmd == "skip-to-after":
        print(skip_to_after(args) or "")
    elif cmd == "set-impl":
        set_impl(args[0], args[1])
    elif cmd == "set-lang":
        set_lang(args[0])
    elif cmd == "auto-migrate":
        print("migrated" if auto_migrate_legacy() else "noop")
    elif cmd == "list-pipelines":
        for name, step, active in list_pipelines():
            marker = "*" if active else " "
            print(f"{marker} {name}: {step}")
    elif cmd == "create-pipeline":
        create_pipeline(args[0])
    elif cmd == "switch-pipeline":
        print("ok" if switch_pipeline(args[0]) else "missing")
    elif cmd == "reset-active":
        reset_active()
    elif cmd == "emit-event":
        kw = dict(arg.split("=", 1) for arg in args[1:])
        emit_event(args[0], **kw)
    elif cmd == "step-file":
        print(STEP_FILE.get(args[0], ""))
    elif cmd == "active-pipeline":
        print(active_pipeline())
    elif cmd == "load":
        s = load()
        print(json.dumps(s, indent=2) if s is not None else "null")
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli()
