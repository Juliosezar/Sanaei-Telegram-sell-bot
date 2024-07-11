import json
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from rest_framework.templatetags.rest_framework import data

from .forms import LoginForm, SearchConfigForm, SearchUserForm, ChangeSettingForm
from django.contrib import messages
from servers.models import Server
from .forms import VpnAppsForm
from django.conf import settings
class LogIn(View):
    formclass = LoginForm
    def get(self, request):
        form = self.formclass
        return render(request, "log_in.html", {"form": form})

    def post(self, request):
        form = self.formclass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd["username"], password=cd["password"])
            if user is not None:
                login(request, user)
                return redirect("accounts:home")
        return render(request, "log_in.html", {"form": form})


class LogOut(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.error(request, "شما از حساب کاربری خود خارج شدید.")
        return redirect("accounts:login")


class HomePage(LoginRequiredMixin, View):
    def get(self, request):
        search_user = SearchUserForm()
        search_config = SearchConfigForm()
        servers = Server.objects.all()
        return render(request, "home.html", {"search_user": search_user,
                                             "search_config": search_config, 'servers':servers})


class SettingsPage(LoginRequiredMixin, View):
    def get(self, request):
        form = ChangeSettingForm()
        return render(request, "settings.html", {"form": form})

    def post(self, request):
        form = ChangeSettingForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            with open("settings.json", "r+") as f:
                data = json.load(f)
                data["pay_card_number"] = cd["card_number"]
                data["pay_card_name"] = cd["card_name"]
                data["prices_msg_id"] = cd["prices_msg_id"]
                data["unlimit_limit"]["1u"]["1m"] = cd["U1_1M"]
                data["unlimit_limit"]["1u"]["2m"] = cd["U1_2M"]
                data["unlimit_limit"]["1u"]["3m"] = cd["U1_3M"]
                data["unlimit_limit"]["2u"]["1m"] = cd["U2_1M"]
                data["unlimit_limit"]["2u"]["2m"] = cd["U2_2M"]
                data["unlimit_limit"]["2u"]["3m"] = cd["U2_3M"]
                data["config_name_counter"] = cd["config_name_counter"]
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            return redirect("accounts:home")
        return render(request, "settings.html", {"form": form})


class VpnAppsPage(LoginRequiredMixin, View):
    def get(self, request):
        with open(settings.BASE_DIR / "settings.json", "r+") as f:
            apps = json.load(f)["applicatios"]
            app_dict = {}
            for ind, app in enumerate(apps):
                app_dict[ind] = app
            print(app_dict)
            return render(request, "show_apps.html", {"apps": app_dict})

class DeleteAppPage(LoginRequiredMixin, View):
    def get(self, request, ind):
        print("asfsf")
        with open(settings.BASE_DIR / "settings.json", "r+") as f:
            file = json.load(f)
            print(file)
            del file["applicatios"][ind]
            f.seek(0)
            json.dump(file, f, indent=4)
            f.truncate()
            return redirect("accounts:vpn_apps")

class AddAppPage(LoginRequiredMixin, View):
    def get(self, request):
        form = VpnAppsForm()
        return render(request, "add_vpn_app.html", {"form": form})

    def post(self, request):
        form = VpnAppsForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            with open(settings.BASE_DIR / "settings.json", "r+") as f:
                file = json.load(f)
                x = {"app_name":cd["app_name"], "download_url":cd["download_url"], "guid" :cd["guid"]}
                file["applicatios"].append(x)
                f.seek(0)
                json.dump(file, f, indent=4)
                f.truncate()
                return redirect("accounts:vpn_apps")
        return render(request, "add_vpn_app.html", {"form": form})
