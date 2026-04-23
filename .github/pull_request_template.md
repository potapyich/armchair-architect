## Summary

<!-- 1-3 bullets: what changed and why -->

## Sync checklist

- [ ] If you changed PRD/plan/impl-plan templates or the per-task execution loop in
      the full pipeline, you also updated `skills/armchair-architect-lite/SKILL.md`
      to match. (See AGENTS.md → "Lite Variant Sync" for the mapping.)
- [ ] If you added or renamed a pipeline step, you updated
      `skills/armchair-architect/lib/steps.json` (single source of truth) — the
      routing table in `SKILL.md` and step file headers will resolve from there.
- [ ] If you changed the `state.json` schema, you also updated `STEP_NAMES`,
      `VALID_EXECUTE`, `VALID_CRITIQUE`, `VALID_LANG` in `lib/state.py` and added
      a smoke test for the new field in `tests/test_state.py`.
- [ ] If you added a new state operation, it lives in `lib/state.py` (not as a
      new inline `python3 -c "..."` snippet). See AGENTS.md → "State helper library".

## Test plan

```
PYTHONPATH=skills/armchair-architect/lib \
  python3 -m unittest discover -s skills/armchair-architect/tests -v
```

<!-- Plus any manual verification in a real pipeline (status, advance, back, skip, etc). -->

