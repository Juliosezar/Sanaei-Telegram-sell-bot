from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
   path("custumers_list/", views.CustomerList.as_view(), name="custumers_list"),
   path("custumer_detail/<int:customer_id>/", views.CustomerDetail.as_view(), name="custumer_detail"),
   path('custumer_configs_api/<str:config_uuid>/', views.GetCustumersConfigsAPI.as_view(), name="custumer_configs_api"),
   path("send_msg_to_all/", views.SendMsgToAll.as_view(), name="send_msg_to_all"),
   path("send_msg_to_Custumer/<int:userid>/", views.SendMsgToUser.as_view(), name="send_msg_to_user"),
   path("change_wallet/<int:userid>/", views.ChangeWalletAmount.as_view(), name="change_wallet"),
   path("update_customer/<int:userid>/", views.UpdateCustumer.as_view(), name="update_customer"),
   path("register_conf_for_customer/<str:conf_uuid>/", views.RegisterConfigToCustumer.as_view(), name="register_conf_for_customer"),
]