from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
   path("custumers_list/", views.CustomerList.as_view(), name="custumers_list"),
   path("custumer_detail/<int:customer_id>/", views.CustomerDetail.as_view(), name="custumer_detail"),
   path('custumer_configs_api/<str:config_uuid>/', views.GetCustumersConfigsAPI.as_view(), name="custumer_configs_api"),
]