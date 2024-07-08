from django.urls import path
from . import views

app_name = "servers"

urlpatterns = [
    path("admin_logs/", views.AdminLogView.as_view(), name="admin_logs"),
    path("pay_logs/", views.PaysLogView.as_view(), name="pay_logs"),
    path("celery_delete_conf_logs/", views.CeleryDeleteConfLogView.as_view(), name="celery_delete_conf_logs"),
    path("send_msgs_log/", views.SendMsgsLogsView.as_view(), name="send_msgs_log"),
    path("delete_msgs/<str:typ>", views.DeleteMsgView.as_view(), name="delete_msgs"),
    path("reports/", views.ReportsView.as_view(), name="reports"),
    path('api', views.ChartData.as_view()),
]
