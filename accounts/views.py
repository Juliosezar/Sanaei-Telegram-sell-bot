from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, SearchConfigForm, SearchUserForm
from django.contrib import messages
from servers.models import Server

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
