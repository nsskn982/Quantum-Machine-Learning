from django import forms
from django.utils.text import slugify

from .models import Entry, Project


class ProjectCreateForm(forms.ModelForm):
    """A new idea from the web. It has no workspace until someone runs new_project for it."""

    class Meta:
        model = Project
        fields = ["title", "track", "difficulty", "summary", "tools", "builds_on", "repo_url"]
        widgets = {"summary": forms.Textarea(attrs={"rows": 4}), "builds_on": forms.CheckboxSelectMultiple}

    def save(self, commit=True):
        project = super().save(commit=False)
        base = slugify(project.title)[:40].strip("-") or "project"
        slug, i = base, 2
        while Project.objects.filter(slug=slug).exists():
            slug, i = f"{base}-{i}", i + 1
        project.slug = slug
        if commit:
            project.save()
            self.save_m2m()
        return project


class ProjectSettingsForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["status", "lead", "repo_url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lead"].queryset = self.instance.members.all()
        self.fields["lead"].required = False


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ["kind", "text"]
        widgets = {"text": forms.Textarea(attrs={"rows": 3, "placeholder": "What did you find, decide or want to try?"})}
