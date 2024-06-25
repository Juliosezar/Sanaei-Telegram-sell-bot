import json

from django import forms
from .models import Users
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate


class UserCreationFormAdminPanel(forms.ModelForm):
    password1 = forms.CharField(label="password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="confirm password", widget=forms.PasswordInput)

    class Meta:
        model = Users
        fields = ("username", "password1", "password2")

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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(label="یوزرنیم:")
    password = forms.CharField(widget=forms.PasswordInput(), label="رمز عبور:")

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValidationError("یوزرنیم یا پسوورد اشتباه است.")


class SearchUserForm(forms.Form):
    search_user = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Search Userid or Username'}))


class SearchConfigForm(forms.Form):
    search_config = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Search Config Name or UUID'}))


class ChangeSettingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("settings.json", "r", encoding="utf-8") as f:
            j = json.load(f)
        self.fields["card_number"].initial = j["pay_card_number"]
        self.fields["card_name"].initial = j["pay_card_name"]
        self.fields["prices_msg_id"].initial = j["prices_msg_id"]
        self.fields["one_usage_limit"].initial = j["one_usage_limit"]
        self.fields["two_usage_limit"].initial = j["two_usage_limit"]
        self.fields["three_usage_limit"].initial = j["three_usage_limit"]


    card_number = forms.IntegerField()
    card_name = forms.CharField(max_length=25)
    prices_msg_id = forms.IntegerField()
    one_usage_limit = forms.IntegerField()
    two_usage_limit = forms.IntegerField()
    three_usage_limit = forms.IntegerField()

    def clean_card_number(self):
        card_number = self.cleaned_data["card_number"]
        if len(str(card_number)) != 16:
            raise ValidationError("شماره کارت باید 16 رقمی باشد.")
        return card_number