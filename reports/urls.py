from django.urls import path
from . import views

app_name = "servers"

urlpatterns = [
    path("admin_logs/", views.AdminLogView.as_view(), name="admin_logs"),
]
