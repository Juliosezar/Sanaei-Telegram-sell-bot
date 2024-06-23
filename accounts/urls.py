from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('login/', views.LogIn.as_view(), name='login'),
    path('logout/', views.LogOut.as_view(), name='logout'),
    path('home/', views.HomePage.as_view(), name='home'),
    path("settings/", views.SettingsPage.as_view(), name='settings'),
]