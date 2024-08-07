from django.urls import path
from . import views

app_name = "servers"

urlpatterns = [
    path("list_configs/<int:server_id>/", views.ListConfigs.as_view(), name="list_configs"),
    path('list_configs_searches/', views.ListConfigsSearched.as_view(), name="list_configs_searches"),
    path("config_page/<int:server_id>/<str:config_uuid>/<str:config_name>/", views.ConfigPage.as_view(), name="conf_page"),
    path('create_config_page/<int:server_id>/<str:form_type>/', views.CreateConfigPage.as_view(), name="create_config_page"),
    path('delete_config/<int:server_id>/<str:config_uuid>/<str:config_name>/<int:inbound_id>/', views.DeleteConfig.as_view(), name="delete_config"),
    path('disable_config/<int:server_id>/<str:config_uuid>/<int:inbound_id>/<str:config_name>/<int:enable>/<int:ip_limit>/', views.DisableConfig.as_view(), name="disable_config"),
    path('show_servers/', views.ShowServers.as_view(), name="show_servers"),
    path("add_server/", views.AddServer.as_view(), name="add_server"),
    path("edit_server/<int:server_id>/", views.EditServer.as_view(), name="edit_server"),
    path("renew_page/<str:uuid>/<str:form_type>/", views.RenewPage.as_view(), name="renew_page"),
    path("change_config_page/<str:config_uuid>/<str:config_name>/<int:server_id>/", views.ChangeConfigPage.as_view(), name="change_config_page"),
    path("api_get_config_time_chices/", views.ApiGetConfigTimeChoices.as_view(), name="api_get_time_choices"),
    path("api_get_config_usage_chices/", views.ApiGetConfigUsageChoices.as_view(), name="api_get_usage_choices"),
    path("api_get_config_ip_limit_chices/", views.ApiGetConfigIPLimitChoices.as_view(), name="api_get_iplimit_choices"),
    path("api_get_axact_price/", views.ApiGetConfigPriceChoices.as_view(), name="api_get_axact_price"),
    path("change_location/<str:config_uuid>/<int:server_id>/", views.ChangeConfigLocationPage.as_view(), name="change_location"),
    path("change_unlimit_limit/<str:config_uuid>/", views.ChangeUnlimitConfLimit.as_view(), name="change_unlimit_limit"),
]
