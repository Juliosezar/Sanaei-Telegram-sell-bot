from django.urls import path
from . import views

app_name = "servers"

urlpatterns = [
    path("list_configs/<int:server_id>/", views.ListConfigs.as_view(), name="list_configs"),
    path('list_configs_searches/', views.ListConfigsSearched.as_view(), name="list_configs_searches"),
]