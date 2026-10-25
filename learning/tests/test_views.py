from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Run
from learning.models import Module, Progress


class SeededTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_portal", verbosity=0, stdout=mock.MagicMock())
        User = get_user_model()
        cls.user = User.objects.create_user("ada", password="x-qubits-42")
        cls.staff = User.objects.create_user("grace", password="x-qubits-42", is_staff=True)

    def setUp(self):
        self.client.force_login(self.user)
        self.m1 = Module.objects.get(number=1)
        self.m5 = Module.objects.get(number=5)


class SeedTests(SeededTestCase):
    def test_modules_are_seeded_idempotently_with_valid_scripts(self):
        call_command("seed_portal", verbosity=0, stdout=mock.MagicMock())
        self.assertEqual(list(Module.objects.values_list("number", flat=True)), list(range(1, 9)))
        for module in Module.objects.all():
            self.assertTrue(module.script_spec().path.is_file(), module.script)

    def test_module_params_match_what_the_scripts_read(self):
        for module in Module.objects.exclude(params={}):
            source = module.source_code()
            for name in module.params:
                self.assertIn(f"{name}=", source, f"{module.script} does not read {name}")


class PageTests(SeededTestCase):
    def test_dashboard_requires_login(self):
        self.client.logout()
        self.assertIn(reverse("login"), self.client.get(reverse("dashboard"))["Location"])

    def test_dashboard_and_module_page(self):
        self.assertContains(self.client.get(reverse("dashboard")), "0<span>/8</span>", html=False)
        response = self.client.get(self.m1.get_absolute_url())
        self.assertContains(response, "Born rule")
        self.assertContains(response, "QuantumCircuit")
        self.assertFalse(Progress.objects.exists())          # viewing is not progress

    def test_saving_progress(self):
        self.client.post(self.m1.get_absolute_url(), {"status": "done", "notes": "clear"})
        self.assertEqual(Progress.objects.get(user=self.user, module=self.m1).status, Progress.Status.DONE)
        self.assertContains(self.client.get(reverse("dashboard")), "1<span>/8</span>", html=False)

    def test_params_form_shown_to_staff_only(self):
        self.assertNotContains(self.client.get(self.m5.get_absolute_url()), 'name="p-n_layers"')
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(self.m5.get_absolute_url()), 'name="p-n_layers"')

    @override_settings(QML_SIGNUP_ENABLED=False)
    def test_signup_can_be_closed(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("signup")).status_code, 404)
        self.assertNotContains(self.client.get(reverse("login")), reverse("signup"))

    def test_unknown_module_is_404(self):
        self.assertEqual(self.client.get("/modules/no-such-module/").status_code, 404)


class ModuleRunViewTests(SeededTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)
        self.url = reverse("module_run", args=[self.m5.slug])

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    @mock.patch("core.services.start_run")
    def test_run_with_params_marks_progress(self, start_run):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, {"p-n_layers": "1", "p-epochs": "5", "p-batch": "25",
                                                   "p-stepsize": "0.2", "p-seed": "1"})
        run = Run.objects.get()
        self.assertRedirects(response, run.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(run.params["n_layers"], 1)
        self.assertEqual(run.params["stepsize"], 0.2)
        start_run.assert_called_once_with(run)
        self.assertEqual(Progress.objects.get(user=self.staff, module=self.m5).status, Progress.Status.IN_PROGRESS)

    @mock.patch("core.services.start_run")
    def test_invalid_params_are_reported_not_run(self, start_run):
        response = self.client.post(self.url, {"p-n_layers": "three"}, follow=True)
        self.assertContains(response, "Check the parameters")
        self.assertFalse(Run.objects.exists())

    @mock.patch("core.services.start_run")
    def test_students_are_refused_by_default(self, start_run):
        self.client.force_login(self.user)
        response = self.client.post(reverse("module_run", args=[self.m1.slug]), follow=True)
        self.assertContains(response, "Only staff accounts")
        self.assertFalse(Run.objects.exists())
