import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("learning", "0001_initial"),
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Run",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(
                    choices=[("queued", "Queued"), ("running", "Running"), ("done", "Finished"), ("failed", "Failed")],
                    default="queued", max_length=10)),
                ("error_kind", models.CharField(
                    blank=True,
                    choices=[("", "No error"), ("timeout", "Timed out"), ("exit_code", "Script error"),
                             ("start_failed", "Could not start"), ("missing_script", "Script missing"),
                             ("invalid_params", "Invalid parameters"), ("stale", "Interrupted"),
                             ("portal_error", "Portal error")],
                    default="", max_length=20)),
                ("params", models.JSONField(blank=True, default=dict)),
                ("metrics", models.JSONField(blank=True, default=dict)),
                ("output", models.TextField(blank=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("started", models.DateTimeField(blank=True, null=True)),
                ("finished", models.DateTimeField(blank=True, null=True)),
                ("experiment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="runs", to="projects.experiment")),
                ("module", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                             related_name="runs", to="learning.module")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                           to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created"]},
        ),
        migrations.AddConstraint(
            model_name="run",
            constraint=models.CheckConstraint(
                condition=(models.Q(("experiment__isnull", True), ("module__isnull", False))
                           | models.Q(("experiment__isnull", False), ("module__isnull", True))),
                name="run_has_exactly_one_target",
            ),
        ),
        migrations.CreateModel(
            name="RunFigure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("file", models.FileField(upload_to="runs/%Y/%m/")),
                ("primary", models.BooleanField(default=False)),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="figures",
                                          to="core.run")),
            ],
            options={"ordering": ["-primary", "name"]},
        ),
    ]
