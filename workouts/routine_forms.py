from django import forms

from .models import RoutineSchedule


class ExerciseCreateForm(forms.Form):
    name = forms.CharField(label="Nombre del ejercicio", max_length=255)
    muscle_group = forms.CharField(label="Grupo muscular", max_length=255)
    type = forms.CharField(label="Tipo", max_length=100)
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
    is_public = forms.BooleanField(label="Rutina publica", required=False)
    scheduled_days = forms.MultipleChoiceField(
        label="Dias asignados",
        required=False,
        choices=RoutineSchedule.DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

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
