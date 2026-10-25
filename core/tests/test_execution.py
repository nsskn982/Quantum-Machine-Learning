"""Tests for the pure-Python run layer. Run with `python manage.py test` or `python -m unittest`."""
import tempfile
import textwrap
import unittest
from pathlib import Path

from core.exceptions import InvalidParams, ScriptUnavailable
from core.execution import DONE, ERR_EXIT, ERR_TIMEOUT, FAILED, execute, merge_params
from core.scripts import ScriptSpec, safe_script_path, validate_param_defaults

QML_LAB = Path(__file__).resolve().parents[2] / "qml_lab"


class SafePathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / "experiments").mkdir()
        (self.base / "experiments" / "e01_baseline.py").write_text("print(1)\n")
        (self.base / "m01_ok.py").write_text("print(1)\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_accepts_files_inside_the_folder(self):
        self.assertEqual(safe_script_path(self.base, "m01_ok.py").name, "m01_ok.py")
        self.assertEqual(safe_script_path(self.base, "experiments/e01_baseline.py").parent.name, "experiments")

    def test_rejects_escapes_and_odd_names(self):
        for bad in ["../m01_ok.py", "/etc/passwd.py", "m01_ok.sh", "a b.py", "m01_ok.py; rm -rf /", "", None,
                    "experiments/../m01_ok.py", "missing.py"]:
            with self.subTest(bad=bad), self.assertRaises(ScriptUnavailable):
                safe_script_path(self.base, bad)

    def test_param_defaults_validation(self):
        self.assertEqual(validate_param_defaults({"n_layers": 3, "lr": 0.1, "noisy": True, "label": "x"}), [])
        self.assertEqual(len(validate_param_defaults({"Bad-Name": 1, "x": [1, 2]})), 2)
        self.assertTrue(validate_param_defaults([1, 2]))


class MergeParamsTests(unittest.TestCase):
    defaults = {"n_layers": 3, "lr": 0.1, "noisy": False, "label": "a"}

    def test_casts_to_default_types(self):
        merged = merge_params(self.defaults, {"n_layers": "5", "lr": "0.02", "noisy": "yes", "label": 7})
        self.assertEqual(merged, {"n_layers": 5, "lr": 0.02, "noisy": True, "label": "7"})

    def test_defaults_when_no_overrides(self):
        self.assertEqual(merge_params(self.defaults, None), self.defaults)

    def test_rejects_unknown_and_bad_values(self):
        for overrides in [{"depth": 2}, {"n_layers": "three"}, {"n_layers": 2.5}, {"lr": "nan"}, {"noisy": "maybe"}]:
            with self.subTest(overrides=overrides), self.assertRaises(InvalidParams):
                merge_params(self.defaults, overrides)


class ExecuteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def spec(self, code, figure="", params=None):
        path = self.base / "script.py"
        path.write_text(textwrap.dedent(code))
        return ScriptSpec("test", path, self.base, figure, params or {}, (QML_LAB,))

    def test_success_collects_output_params_figures_and_metrics(self):
        spec = self.spec("""
            from plots import params, log_metrics, FIG_DIR
            P = params(n=2, scale=1.5)
            (FIG_DIR / "b.png").write_bytes(b"b")
            (FIG_DIR / "main.png").write_bytes(b"main")
            log_metrics(accuracy=0.75 * P.scale, n=P.n)
            print("hello")
        """, figure="main.png", params={"n": 2, "scale": 1.5})
        result = execute(spec, {"n": 4, "scale": 1.0}, timeout=60)
        self.assertEqual(result.status, DONE, result.output)
        self.assertIn("hello", result.output)
        self.assertIn("params: n=4, scale=1.0", result.output)
        self.assertEqual([name for name, _ in result.figures], ["main.png", "b.png"])
        self.assertEqual(result.metrics, {"accuracy": 0.75, "n": 4.0})

    def test_failing_script_reports_exit_code_and_traceback(self):
        result = execute(self.spec("raise ValueError('boom')\n"), {}, timeout=60)
        self.assertEqual((result.status, result.error_kind, result.returncode), (FAILED, ERR_EXIT, 1))
        self.assertIn("ValueError: boom", result.output)

    def test_timeout(self):
        result = execute(self.spec("import time\nprint('started', flush=True)\ntime.sleep(10)\n"), {}, timeout=1)
        self.assertEqual((result.status, result.error_kind), (FAILED, ERR_TIMEOUT))
        self.assertIn("Stopped after 1 s", result.output)

    def test_bad_metrics_and_missing_figure_are_warnings_not_failures(self):
        spec = self.spec("""
            import json, os, pathlib
            out = pathlib.Path(os.environ["QML_FIG_DIR"])
            (out / "metrics.json").write_text(json.dumps({"ok": 1.0, "bad": "text", "flag": True}))
        """, figure="expected.png")
        result = execute(spec, {}, timeout=60)
        self.assertEqual(result.status, DONE)
        self.assertEqual(result.metrics, {"ok": 1.0})
        self.assertIn("metric 'bad' ignored", result.output)
        self.assertIn("expected figure expected.png was not produced", result.output)

    def test_unreadable_metrics_file(self):
        spec = self.spec("""
            import os, pathlib
            (pathlib.Path(os.environ["QML_FIG_DIR"]) / "metrics.json").write_text("{not json")
        """)
        result = execute(spec, {}, timeout=60)
        self.assertEqual(result.status, DONE)
        self.assertIn("metrics.json ignored", result.output)

    def test_params_reach_the_script_as_json(self):
        spec = self.spec("import os, json\nprint(json.loads(os.environ['QML_PARAMS']))\n")
        result = execute(spec, {"a": 1}, timeout=60)
        self.assertIn("{'a': 1}", result.output)


if __name__ == "__main__":
    unittest.main()
