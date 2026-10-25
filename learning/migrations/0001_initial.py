import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Module",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveSmallIntegerField(unique=True)),
                ("slug", models.SlugField(unique=True)),
                ("title", models.CharField(max_length=120)),
                ("week", models.CharField(help_text="e.g. '5-6'", max_length=20)),
                ("tool", models.CharField(help_text="Main framework used", max_length=80)),
                ("summary", models.CharField(max_length=240)),
                ("concept", models.TextField(help_text="Plain-text explanation; blank lines split paragraphs")),
                ("formula", models.TextField(blank=True, help_text="LaTeX, rendered with MathJax")),
                ("script", models.CharField(help_text="File in qml_lab/, e.g. m01_qubits.py", max_length=80)),
                ("figure", models.CharField(help_text="PNG the script saves, e.g. m01_bloch.png", max_length=80)),
                ("figure_caption", models.TextField(blank=True)),
                ("checkpoint", models.TextField()),
                ("params", models.JSONField(blank=True, default=dict,
                                            help_text="Parameter defaults the script reads via params()")),
            ],
            options={"ordering": ["number"]},
        ),
        migrations.CreateModel(
            name="Progress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(
                    choices=[("not_started", "Not started"), ("in_progress", "In progress"), ("done", "Checkpoint passed")],
                    default="not_started", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress",
                                             to="learning.module")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress",
                                           to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="progress",
            constraint=models.UniqueConstraint(fields=("user", "module"), name="one_progress_per_module"),
        ),
    ]
