from django import forms

from .models import Progress


class ProgressForm(forms.ModelForm):
    class Meta:
        model = Progress
        fields = ["status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 4, "placeholder": "What clicked, what didn't, questions for later"})}
