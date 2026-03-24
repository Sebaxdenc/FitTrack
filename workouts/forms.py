from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import Profile


User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario", max_length=150)
    password = forms.CharField(label="Contrasena", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Credenciales invalidas. Intenta nuevamente.")
            cleaned_data["user"] = user
        return cleaned_data

    def _apply_styles(self):
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "placeholder": field.label,
                    "class": "input-control",
                    "id": f"login_{name}",
                    "autocomplete": "username" if name == "username" else "current-password",
                }
            )


class RegistrationForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre", max_length=30)
    last_name = forms.CharField(label="Apellido", max_length=150)
    email = forms.EmailField(label="Correo")
    password1 = forms.CharField(label="Contrasena", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contrasena", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

    def clean(self):
        cleaned_data = super().clean()
        pwd1 = cleaned_data.get("password1")
        pwd2 = cleaned_data.get("password2")
        if pwd1 and pwd2:
            if pwd1 != pwd2:
                raise forms.ValidationError("Las contrasenas no coinciden.")
            validate_password(pwd1)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            Profile.objects.get_or_create(user=user)
        return user

    def _apply_styles(self):
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "placeholder": field.label,
                    "class": "input-control",
                    "id": f"reg_{name}",
                }
            )
