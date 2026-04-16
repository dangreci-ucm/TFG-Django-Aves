from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, label="Nombre de usuario")
    email = forms.EmailField(label="Correo electrónico")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Repetir contraseña")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ese nombre de usuario ya existe.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ese correo ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        if password1:
            validate_password(password1)

        return cleaned_data


class VerifyCodeForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    code = forms.CharField(max_length=6, min_length=6, label="Código")


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        return email


class ResetPasswordForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    code = forms.CharField(max_length=6, min_length=6, label="Código")
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="Nueva contraseña")
    new_password2 = forms.CharField(widget=forms.PasswordInput, label="Repetir nueva contraseña")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        if password1:
            validate_password(password1)

        return cleaned_data