"""Django-level tests for runs: the service, the runner and the run page."""
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from core.exceptions import RunAlreadyActive, RunRefused
from core.models import Run
from core.runner import execute_run, fail_stale_runs
from core.services import request_run
from learning.models import Module

QML_LAB = Path(__file__).resolve().parents[2] / "qml_lab"


class LabTestCase(TestCase):
    """A temporary qml_lab with a few tiny scripts that use the real plots.py helpers."""

    scripts = {
        "m91_ok.py": "from plots import params, log_metrics, FIG_DIR\nP = params(n=1)\n"
                     "(FIG_DIR / 'm91_ok.png').write_bytes(b'png')\nlog_metrics(score=P.n * 0.5)\nprint('ran', P.n)\n",
        "m92_crash.py": "raise RuntimeError('broken on purpose')\n",
    }

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        lab = Path(self.tmp.name) / "lab"
        lab.mkdir()
        (lab / "plots.py").write_text((QML_LAB / "plots.py").read_text())
        for name, code in self.scripts.items():
            (lab / name).write_text(code)
        self.override = override_settings(QML_LAB_DIR=lab, MEDIA_ROOT=Path(self.tmp.name) / "media")
        self.override.enable()
        User = get_user_model()
        self.staff = User.objects.create_user("grace", password="x-qubits-42", is_staff=True)
        self.student = User.objects.create_user("ada", password="x-qubits-42")

    def tearDown(self):
        self.override.disable()
        self.tmp.cleanup()

    def module(self, number, script, params=None):
        return Module.objects.create(number=number, slug=f"m{number}", title="T", week="1", tool="-", summary="s",
                                     concept="c", script=script, figure=script.replace(".py", ".png"),
                                     checkpoint="k", params=params or {})


class RequestRunTests(LabTestCase):
    @mock.patch("core.services.start_run")
    def test_starts_after_commit_with_merged_params(self, start_run):
        module = self.module(91, "m91_ok.py", {"n": 1})
        with self.captureOnCommitCallbacks(execute=True):
            run = request_run(self.staff, module, {"n": "3"})
        self.assertEqual(run.params, {"n": 3})
        start_run.assert_called_once_with(run)

    def test_refusals(self):
        module = self.module(91, "m91_ok.py", {"n": 1})
        with self.assertRaisesRegex(RunRefused, "staff"):
            request_run(self.student, module)
        with self.assertRaisesRegex(RunRefused, "Unknown parameter"):
            request_run(self.staff, module, {"depth": 2})
        with self.assertRaisesRegex(RunRefused, "not found"):
            request_run(self.staff, self.module(93, "m93_missing.py"))
        with override_settings(QML_RUNS_ENABLED=False), self.assertRaisesRegex(RunRefused, "turned off"):
            request_run(self.staff, module)
        self.assertFalse(Run.objects.exists())

    @mock.patch("core.services.start_run")
    def test_active_run_is_reused_and_stale_runs_are_cleared(self, start_run):
        module = self.module(91, "m91_ok.py")
        active = Run.objects.create(module=module, status=Run.Status.RUNNING)
        with self.assertRaises(RunAlreadyActive) as ctx:
            request_run(self.staff, module)
        self.assertEqual(ctx.exception.run, active)
        Run.objects.filter(pk=active.pk).update(created=timezone.now() - timedelta(days=1))
        request_run(self.staff, module)
        active.refresh_from_db()
        self.assertEqual((active.status, active.error_kind), (Run.Status.FAILED, Run.ErrorKind.STALE))


@mock.patch("core.runner.close_old_connections")     # keep the test transaction open
class ExecuteRunTests(LabTestCase):
    def test_success_stores_figure_metrics_and_output(self, _):
        run = Run.objects.create(module=self.module(91, "m91_ok.py", {"n": 1}), params={"n": 4})
        execute_run(run.pk)
        run.refresh_from_db()
        self.assertEqual(run.status, Run.Status.DONE, run.output)
        self.assertEqual(run.metrics, {"score": 2.0})
        self.assertIn("ran 4", run.output)
        self.assertEqual(run.primary_figure.name, "m91_ok.png")
        self.assertTrue(run.primary_figure.primary)

    def test_script_error_is_recorded(self, _):
        run = Run.objects.create(module=self.module(92, "m92_crash.py"))
        execute_run(run.pk)
        run.refresh_from_db()
        self.assertEqual((run.status, run.error_kind), (Run.Status.FAILED, Run.ErrorKind.EXIT_CODE))
        self.assertIn("broken on purpose", run.output)

    def test_missing_script_is_recorded(self, _):
        run = Run.objects.create(module=self.module(93, "m93_missing.py"))
        execute_run(run.pk)
        run.refresh_from_db()
        self.assertEqual(run.error_kind, Run.ErrorKind.MISSING_SCRIPT)

    def test_unexpected_portal_error_never_leaves_a_run_running(self, _):
        run = Run.objects.create(module=self.module(91, "m91_ok.py"))
        with mock.patch("core.runner.execute", side_effect=OSError("disk full")), self.assertLogs("qml.runs", "ERROR"):
            execute_run(run.pk)
        run.refresh_from_db()
        self.assertEqual((run.status, run.error_kind), (Run.Status.FAILED, Run.ErrorKind.PORTAL_ERROR))

    def test_fail_stale_runs_leaves_recent_runs_alone(self, _):
        module = self.module(91, "m91_ok.py")
        recent = Run.objects.create(module=module, status=Run.Status.RUNNING)
        old = Run.objects.create(module=module, status=Run.Status.QUEUED)
        Run.objects.filter(pk=old.pk).update(created=timezone.now() - timedelta(days=1))
        with self.assertLogs("qml.runs", "WARNING"):
            self.assertEqual(fail_stale_runs(), 1)
        recent.refresh_from_db()
        self.assertEqual(recent.status, Run.Status.RUNNING)


class RunPageTests(LabTestCase):
    def test_run_page_explains_errors_and_refreshes_while_active(self):
        self.client.force_login(self.student)
        run = Run.objects.create(module=self.module(91, "m91_ok.py"), status=Run.Status.RUNNING)
        self.assertContains(self.client.get(run.get_absolute_url()), 'http-equiv="refresh"')
        Run.objects.filter(pk=run.pk).update(status=Run.Status.FAILED, error_kind=Run.ErrorKind.TIMEOUT)
        response = self.client.get(run.get_absolute_url())
        self.assertNotContains(response, 'http-equiv="refresh"')
        self.assertContains(response, "QML_RUN_TIMEOUT")

    def test_a_run_needs_exactly_one_target(self):
        from django.db import IntegrityError, transaction
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Run.objects.create()
