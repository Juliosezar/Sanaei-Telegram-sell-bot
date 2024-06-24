from .models import Users
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserCreationFormAdminPanel, UserEditFormAdminPanel
from django.contrib.auth.models import Group
from django.contrib import admin


class UserAdmin(BaseUserAdmin):
    form = UserEditFormAdminPanel
    add_form = UserCreationFormAdminPanel


    list_display = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("permitions", {"fields": (),}),
    )

    add_fieldsets = (
        (None, {"fields": ("username", "password1", "password2")}),
        ("permitions", {"fields": (),}),
    )

    filter_horizontal = ()


admin.site.unregister(Group)
admin.site.register(Users)