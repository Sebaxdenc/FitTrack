from django import forms

from .models import RoutineSchedule


class ExerciseCreateForm(forms.Form):
    name = forms.CharField(label="Nombre del ejercicio", max_length=255)
    muscle_group = forms.CharField(label="Grupo muscular", max_length=255)
    description = forms.CharField(
        label="Descripcion",
        widget=forms.Textarea(attrs={"rows": 4}),
        max_length=1000,
    )
    image_url = forms.CharField(label="Foto URL opcional", required=False)
    equipment_photo = forms.ImageField(label="Foto del equipo", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

    def clean_image_url(self):
        value = (self.cleaned_data.get("image_url") or "").strip()
        if value and not (value.startswith("http://") or value.startswith("https://")):
            raise forms.ValidationError("La foto debe usar http:// o https://")
        return value

    def _apply_styles(self):
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "class": "input-control",
                    "id": f"exercise_{name}",
                    "placeholder": field.label,
                }
            )
        self.fields["equipment_photo"].widget.attrs["accept"] = "image/*"


class RoutineCreateForm(forms.Form):
    name = forms.CharField(label="Nombre de la rutina", max_length=255)
    goal = forms.CharField(label="Objetivo", max_length=255, required=False)
    VISIBILITY_CHOICES = (
        ("True", "Público"),
        ("False", "Privado"),
    )
    is_public = forms.ChoiceField(label="Visibilidad", choices=VISIBILITY_CHOICES, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

    def _apply_styles(self):
        for name, field in self.fields.items():
            if name == "scheduled_days":
                continue
            field.widget.attrs.update(
                {
                    "class": "input-control",
                    "id": f"routine_{name}",
                    "placeholder": field.label,
                }
            )

    def clean_is_public(self):
        val = self.cleaned_data.get("is_public")
        return True if val == "True" else False
