"""Smoke tests for lib/state.py.

Run with:
    PYTHONPATH=skills/armchair-architect/lib python3 -m unittest discover -s skills/armchair-architect/tests -v

Each test runs in a temp directory so .pipeline/ writes don't leak into the repo.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

import state


class TempPipelineCase(unittest.TestCase):
    """Base: chdir into a temp dir, seed a default pipeline, restore on teardown."""

    def setUp(self):
        self._prev_cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="aa_state_test_")
        os.chdir(self._tmp)
        Path(".pipeline/default").mkdir(parents=True)
        Path(".pipeline/active").write_text("default")
        self._seed_state({
            "step": "init",
            "completed": [],
            "pending": list(state.STEP_NAMES),
            "impl": {"interview": "ask_user_question", "execute": "default", "critique": "none"},
        })

    def tearDown(self):
        os.chdir(self._prev_cwd)
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _seed_state(self, s):
        with open(".pipeline/default/state.json", "w") as f:
            json.dump(s, f)


class TestStepsManifest(unittest.TestCase):
    def test_steps_loaded_from_json(self):
        self.assertGreater(len(state.STEPS), 0)
        self.assertEqual(state.STEP_NAMES[0], "init")
        self.assertEqual(state.STEP_NAMES[-1], "execute")

    def test_step_file_lookup(self):
        for name in state.STEP_NAMES:
            self.assertTrue(state.STEP_FILE[name].endswith(".md"))


class TestAdvance(TempPipelineCase):
    def test_advance_through_full_pipeline(self):
        for expected_next in state.STEP_NAMES[1:] + ["done"]:
            self.assertEqual(state.advance(), expected_next)
        s = state.load()
        self.assertEqual(s["step"], "done")
        self.assertEqual(s["completed"], state.STEP_NAMES)
        self.assertEqual(s["pending"], [])


class TestSetters(TempPipelineCase):
    def test_set_impl(self):
        state.set_impl("execute", "ralph")
        self.assertEqual(state.load()["impl"]["execute"], "ralph")

    def test_set_lang(self):
        state.set_lang("ru")
        self.assertEqual(state.load()["lang"], "ru")


class TestRollback(TempPipelineCase):
    def test_rollback_one_after_advance(self):
        state.advance()
        state.advance()
        prev = state.rollback_one()
        self.assertEqual(prev, "setup")
        s = state.load()
        self.assertEqual(s["step"], "setup")
        self.assertIn("setup", s["pending"])
        self.assertNotIn("setup", s["completed"])

    def test_rollback_one_at_start_returns_none(self):
        self.assertIsNone(state.rollback_one())

    def test_rollback_to_moves_all_later_steps_back(self):
        for _ in range(5):
            state.advance()
        s_before = state.load()
        self.assertEqual(s_before["step"], "impl_plan")

        state.rollback_to("plan")

        s = state.load()
        self.assertEqual(s["step"], "plan")
        self.assertNotIn("plan", s["completed"])
        self.assertNotIn("impl_plan", s["completed"])
        self.assertEqual(s["pending"][:2], ["plan", "impl_plan"])

    def test_rollback_to_unknown_step_raises(self):
        with self.assertRaises(ValueError):
            state.rollback_to("not_a_real_step")


class TestSkip(TempPipelineCase):
    def test_skip_marks_steps_completed(self):
        nxt = state.skip_to_after(["init", "setup"])
        self.assertEqual(nxt, "interview_setup")
        s = state.load()
        self.assertIn("init", s["completed"])
        self.assertIn("setup", s["completed"])
        self.assertNotIn("init", s["pending"])


class TestValidate(TempPipelineCase):
    def test_clean_state_validates(self):
        self.assertEqual(state.validate(), [])

    def test_unknown_step_caught(self):
        self._seed_state({"step": "bogus", "completed": [], "pending": ["bogus"], "impl": {}})
        errs = state.validate()
        self.assertTrue(any("unknown step" in e for e in errs))

    def test_overlap_caught(self):
        self._seed_state({
            "step": "interview",
            "completed": ["init", "setup"],
            "pending": ["setup", "interview"],
            "impl": {},
        })
        errs = state.validate()
        self.assertTrue(any("both pending and completed" in e for e in errs))

    def test_unknown_impl_execute_caught(self):
        self._seed_state({
            "step": "init",
            "completed": [],
            "pending": ["init"],
            "impl": {"execute": "bogus_executor"},
        })
        errs = state.validate()
        self.assertTrue(any("unknown impl.execute" in e for e in errs))

    def test_unknown_lang_caught(self):
        self._seed_state({
            "step": "init",
            "completed": [],
            "pending": ["init"],
            "lang": "fr",
            "impl": {},
        })
        errs = state.validate()
        self.assertTrue(any("unknown lang" in e for e in errs))

    def test_step_must_be_in_pending(self):
        self._seed_state({
            "step": "interview",
            "completed": [],
            "pending": ["init"],
            "impl": {},
        })
        errs = state.validate()
        self.assertTrue(any("not in pending" in e for e in errs))


class TestMigration(unittest.TestCase):
    def setUp(self):
        self._prev_cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="aa_migrate_test_")
        os.chdir(self._tmp)

    def tearDown(self):
        os.chdir(self._prev_cwd)
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_legacy_state_migrated(self):
        Path(".pipeline").mkdir()
        Path(".pipeline/state.json").write_text('{"step":"init","completed":[],"pending":["init"]}')
        self.assertTrue(state.auto_migrate_legacy())
        self.assertFalse(Path(".pipeline/state.json").exists())
        self.assertTrue(Path(".pipeline/default/state.json").exists())
        self.assertEqual(Path(".pipeline/active").read_text(), "default")

    def test_no_migration_when_active_exists(self):
        Path(".pipeline/feature-x").mkdir(parents=True)
        Path(".pipeline/active").write_text("feature-x")
        Path(".pipeline/feature-x/state.json").write_text('{"step":"init"}')
        self.assertFalse(state.auto_migrate_legacy())

    def test_specialized_renamed_to_default(self):
        Path(".pipeline/default").mkdir(parents=True)
        Path(".pipeline/active").write_text("default")
        Path(".pipeline/default/state.json").write_text(
            '{"step":"init","completed":[],"pending":["init"],"impl":{"execute":"specialized"}}'
        )
        self.assertTrue(state.auto_migrate_legacy())
        with open(".pipeline/default/state.json") as f:
            import json
            s = json.load(f)
        self.assertEqual(s["impl"]["execute"], "default")

    def test_migration_idempotent(self):
        Path(".pipeline/default").mkdir(parents=True)
        Path(".pipeline/active").write_text("default")
        Path(".pipeline/default/state.json").write_text(
            '{"step":"init","completed":[],"pending":["init"],"impl":{"execute":"default"}}'
        )
        self.assertFalse(state.auto_migrate_legacy())

    def test_first_run_bootstrap_creates_state(self):
        # Pristine project — no .pipeline/ at all
        self.assertTrue(state.auto_migrate_legacy())
        self.assertEqual(Path(".pipeline/active").read_text(), "default")
        s = state.load()
        self.assertEqual(s["step"], "init")
        self.assertEqual(s["completed"], [])
        self.assertEqual(s["pending"], list(state.STEP_NAMES))
        self.assertEqual(s["impl"]["execute"], "default")
        # Subsequent advance must work without crashing
        nxt = state.advance()
        self.assertEqual(nxt, "setup")


class TestMultiPipeline(TempPipelineCase):
    def test_create_and_switch(self):
        state.create_pipeline("feature-auth")
        self.assertEqual(state.active_pipeline(), "feature-auth")
        # Seed the new pipeline so switch_pipeline can find its state file
        Path(".pipeline/feature-auth/state.json").write_text('{"step":"init","completed":[],"pending":["init"]}')

        self.assertTrue(state.switch_pipeline("default"))
        self.assertEqual(state.active_pipeline(), "default")
        self.assertTrue(state.switch_pipeline("feature-auth"))
        self.assertEqual(state.active_pipeline(), "feature-auth")

    def test_switch_to_missing_pipeline_returns_false(self):
        self.assertFalse(state.switch_pipeline("nonexistent"))

    def test_list_pipelines_marks_active(self):
        Path(".pipeline/other").mkdir()
        Path(".pipeline/other/state.json").write_text('{"step":"init"}')
        rows = state.list_pipelines()
        names = {name: active for (name, _step, active) in rows}
        self.assertTrue(names["default"])
        self.assertFalse(names["other"])

    def test_reset_active_removes_state_only(self):
        state.reset_active()
        self.assertFalse(Path(".pipeline/default/state.json").exists())
        # active marker stays — it just points to an empty pipeline now
        self.assertEqual(Path(".pipeline/active").read_text(), "default")


class TestEvents(TempPipelineCase):
    def test_emit_and_read(self):
        state.emit_event("task_pass", id="1.1", attempts="1", category="backend")
        state.emit_event("task_stuck", id="1.2", category="frontend")
        events = state.read_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["event"], "task_pass")
        self.assertEqual(events[0]["id"], "1.1")
        self.assertEqual(events[1]["event"], "task_stuck")

    def test_read_events_missing_file_returns_empty(self):
        self.assertEqual(state.read_events(), [])

    def test_emit_never_raises(self):
        # Pass a non-string kwarg value — should still serialize fine
        state.emit_event("noop", count=5)
        self.assertEqual(state.read_events()[0]["count"], 5)


if __name__ == "__main__":
    unittest.main()
