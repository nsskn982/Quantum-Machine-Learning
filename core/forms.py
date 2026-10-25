from django import forms


class ParamsForm(forms.Form):
    """A form built from a script's parameter defaults (bool, int, float or text)."""

    def __init__(self, defaults, *args, **kwargs):
        kwargs.setdefault("prefix", "p")
        super().__init__(*args, **kwargs)
        for name, value in (defaults or {}).items():
            label = name.replace("_", " ").capitalize()
            if isinstance(value, bool):
                field = forms.BooleanField(required=False, initial=value, label=label)
            elif isinstance(value, int):
                field = forms.IntegerField(initial=value, label=label)
            elif isinstance(value, float):
                field = forms.FloatField(initial=value, label=label)
            else:
                field = forms.CharField(initial=value, label=label, max_length=200)
            field.help_text = f"default {value}"
            self.fields[name] = field
