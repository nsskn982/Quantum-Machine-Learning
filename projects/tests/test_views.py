import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Run
from projects.models import Entry, Experiment, Project
from projects.sync import sync_projects

SHIPPED = Path(__file__).resolve().parents[2] / "qml_projects"
QUIET = {"verbosity": 0, "stdout": mock.MagicMock()}


class WorkspaceTestCase(TestCase):
    """Each test gets a writable copy of the shipped workspaces."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "qml_projects"
        shutil.copytree(SHIPPED, self.root)
        self.override = override_settings(QML_PROJECTS_DIR=self.root)
        self.override.enable()
        call_command("seed_portal", **QUIET)
        User = get_user_model()
        self.ada = User.objects.create_user("ada", password="x-qubits-42")
        self.alan = User.objects.create_user("alan", password="x-qubits-42")
        self.staff = User.objects.create_user("grace", password="x-qubits-42", is_staff=True)
        self.client.force_login(self.ada)
        self.project = Project.objects.get(slug="reuploading-depth-mnist")

    def tearDown(self):
        self.override.disable()
        self.tmp.cleanup()


class SyncTests(WorkspaceTestCase):
    def test_all_sixteen_workspaces_are_loaded_with_modules_and_experiments(self):
        self.assertEqual(Project.objects.count(), 16)
        self.assertEqual(list(self.project.builds_on.values_list("number", flat=True)), [5])
        exp = self.project.experiments.get()
        self.assertEqual(exp.params["n_layers"], 2)
        self.assertTrue(exp.script_spec().path.is_file())
        self.assertIn("Open questions", self.project.readme())

    def test_resync_keeps_people_status_and_journal(self):
        self.client.post(reverse("project_join", args=[self.project.slug]))
        Entry.objects.create(project=self.project, author=self.ada, text="keep me")
        sync_projects()
        self.project.refresh_from_db()
        self.assertEqual((self.project.lead, self.project.status), (self.ada, Project.Status.ACTIVE))
        self.assertEqual(self.project.entries.count(), 1)

    def test_removed_experiment_is_deactivated_not_deleted(self):
        manifest = self.root / self.project.slug / "project.toml"
        manifest.write_text(manifest.read_text().split("[[experiments]]")[0])
        sync_projects()
        exp = Experiment.objects.get(project=self.project)
        self.assertFalse(exp.active)

    def test_a_broken_workspace_does_not_stop_the_others(self):
        (self.root / "quantum-autoencoder" / "project.toml").write_text("title = \n")
        report = sync_projects()
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(len(report.created) + len(report.updated), 15)
        with self.assertRaises(CommandError):
            call_command("sync_projects", "--strict", **QUIET)

    def test_new_project_command_builds_a_workspace_for_a_web_idea(self):
        self.client.post(reverse("project_create"), {"title": "Quantum walk search", "track": "variational",
                                                     "difficulty": "hard", "summary": "Search with walks",
                                                     "tools": "PennyLane", "repo_url": ""})
        web = Project.objects.get(slug="quantum-walk-search")
        self.assertEqual((web.lead, web.workspace), (self.ada, ""))
        call_command("new_project", "quantum-walk-search", **QUIET)
        web.refresh_from_db()
        self.assertEqual(web.workspace, "quantum-walk-search")
        self.assertEqual(web.lead, self.ada)                         # people survive the sync
        self.assertTrue(web.experiments.get(slug="starter").script_spec().path.is_file())
        with self.assertRaises(CommandError):
            call_command("new_project", "quantum-walk-search", **QUIET)   # already exists
        with self.assertRaises(CommandError):
            call_command("new_project", "brand-new", **QUIET)             # nothing to copy details from


class MembershipTests(WorkspaceTestCase):
    def test_join_makes_first_member_lead_and_project_active(self):
        self.client.post(reverse("project_join", args=[self.project.slug]))
        self.project.refresh_from_db()
        self.assertEqual((self.project.lead, self.project.status), (self.ada, Project.Status.ACTIVE))
        self.assertIn(self.project, self.ada.qml_projects.all())

    def test_several_people_can_join_and_lead_passes_on(self):
        self.client.post(reverse("project_join", args=[self.project.slug]))
        self.client.force_login(self.alan)
        self.client.post(reverse("project_join", args=[self.project.slug]))
        self.client.force_login(self.ada)
        self.client.post(reverse("project_leave", args=[self.project.slug]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.lead, self.alan)
        self.client.force_login(self.alan)
        self.client.post(reverse("project_leave", args=[self.project.slug]))
        self.project.refresh_from_db()
        self.assertEqual((self.project.lead, self.project.status), (None, Project.Status.OPEN))

    def test_only_members_write_journal_and_settings(self):
        url = reverse("entry_create", args=[self.project.slug])
        self.client.post(url, {"kind": "note", "text": "outsider"})
        self.assertFalse(Entry.objects.exists())
        self.client.post(reverse("project_join", args=[self.project.slug]))
        self.client.post(url, {"kind": "result", "text": "4 qubits, 2 layers: 0.93"})
        self.assertEqual(Entry.objects.get().kind, "result")
        self.client.post(reverse("project_settings", args=[self.project.slug]),
                         {"status": "paused", "lead": self.ada.pk, "repo_url": ""})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.PAUSED)

    def test_archived_projects_are_hidden_and_cannot_be_joined(self):
        Project.objects.filter(pk=self.project.pk).update(status=Project.Status.ARCHIVED)
        self.assertNotContains(self.client.get(reverse("project_list")), self.project.title)
        self.assertContains(self.client.get(reverse("project_list"), {"status": "archived"}), self.project.title)
        self.client.post(reverse("project_join", args=[self.project.slug]))
        self.assertFalse(self.project.members.exists())

    def test_list_filters_and_detail_page(self):
        response = self.client.get(reverse("project_list"), {"track": "kernels", "difficulty": "nonsense"})
        self.assertContains(response, "Trainable quantum kernels")
        self.assertNotContains(response, "Quantum autoencoder")
        detail = self.client.get(self.project.get_absolute_url())
        self.assertContains(detail, "Re-uploading classifier vs logistic regression")
        self.assertContains(detail, "Open questions")


class ExperimentRunTests(WorkspaceTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("experiment_run", args=[self.project.slug, "baseline"])

    @mock.patch("core.services.start_run")
    def test_staff_run_with_params_is_logged_in_the_journal(self, start_run):
        self.client.force_login(self.staff)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url, {"p-digit_a": "4", "p-digit_b": "9", "p-n_qubits": "4",
                                        "p-n_layers": "3", "p-epochs": "5", "p-seed": "0"})
        run = Run.objects.get()
        self.assertEqual((run.experiment.slug, run.params["n_layers"]), ("baseline", 3))
        start_run.assert_called_once_with(run)
        self.assertEqual(Entry.objects.get().run, run)

    @mock.patch("core.services.start_run")
    def test_non_members_cannot_run(self, start_run):
        self.client.post(self.url, {})
        self.assertFalse(Run.objects.exists())

    def test_script_download_and_unknown_experiment(self):
        response = self.client.get(reverse("experiment_script", args=[self.project.slug, "baseline"]))
        self.assertIn("e01_baseline.py", response["Content-Disposition"])
        self.assertEqual(self.client.get(reverse("experiment_script", args=[self.project.slug, "nope"])).status_code, 404)
