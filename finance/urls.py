from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path('confirm_payment/', views.ConfirmPayment.as_view(), name='confirm_payments'),
]