import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("learning", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveSmallIntegerField(blank=True, help_text="Position in the plan's list", null=True)),
                ("slug", models.SlugField(unique=True)),
                ("title", models.CharField(max_length=120)),
                ("track", models.CharField(
                    choices=[("kernels", "Kernels"), ("variational", "Variational"), ("hybrid", "Hybrid"),
                             ("quantum_data", "Quantum data"), ("noise_hardware", "Noise and hardware")],
                    max_length=20)),
                ("difficulty", models.CharField(choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
                                                max_length=10)),
                ("summary", models.TextField()),
                ("tools", models.CharField(blank=True, max_length=120)),
                ("status", models.CharField(
                    choices=[("open", "Looking for people"), ("active", "Active"), ("paused", "Paused"),
                             ("archived", "Archived")],
                    default="open", max_length=20)),
                ("repo_url", models.URLField(blank=True)),
                ("workspace", models.CharField(blank=True, help_text="Folder name under qml_projects/", max_length=80)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("builds_on", models.ManyToManyField(blank=True, related_name="projects", to="learning.module")),
                ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                           related_name="led_qml_projects", to=settings.AUTH_USER_MODEL)),
                ("members", models.ManyToManyField(blank=True, related_name="qml_projects", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": [models.F("number").asc(nulls_last=True), "title"]},
        ),
        migrations.CreateModel(
            name="Experiment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField()),
                ("title", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("script", models.CharField(help_text="Path inside the workspace, e.g. experiments/e01_baseline.py",
                                            max_length=200)),
                ("figure", models.CharField(blank=True, max_length=120)),
                ("params", models.JSONField(blank=True, default=dict)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("active", models.BooleanField(default=True,
                                               help_text="False once removed from project.toml (runs are kept)")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="experiments",
                                              to="projects.project")),
            ],
            options={"ordering": ["order", "slug"]},
        ),
        migrations.AddConstraint(
            model_name="experiment",
            constraint=models.UniqueConstraint(fields=("project", "slug"), name="unique_experiment_per_project"),
        ),
        migrations.CreateModel(
            name="Entry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(
                    choices=[("note", "Note"), ("result", "Result"), ("decision", "Decision"),
                             ("question", "Open question"), ("next_step", "Next step")],
                    default="note", max_length=20)),
                ("text", models.TextField()),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                             to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="entries",
                                              to="projects.project")),
            ],
            options={"ordering": ["-created"], "verbose_name_plural": "entries"},
        ),
    ]
