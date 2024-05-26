from django import forms
from .models import Users
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate



class UserCreationFormAdminPanel(forms.ModelForm):
    password1 = forms.CharField(label="password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="confirm password", widget=forms.PasswordInput)

    class Meta:
        model = Users
        fields = ("username", "password", "password2")

    def clean_password2(self):
        cd = self.cleaned_data
        if cd["password1"] and cd["password2"] and cd["password1"] != cd["password2"]:
            raise ValidationError("passwords dont match !!")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserEditFormAdminPanel(forms.ModelForm):
    class Meta:
        model = Users
        fields = ("username", "password")


class LoginForm(forms.Form):
    username = forms.CharField(label="یوزرنیم:")
    password = forms.CharField(widget=forms.PasswordInput(), label="رمز عبور:")

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValidationError("یوزرنیم یا پسوورد اشتباه است.")

