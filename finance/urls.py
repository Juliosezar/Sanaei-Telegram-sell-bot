from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path('confirm_payment/', views.ConfirmPaymentPage.as_view(), name='confirm_payments'),
    path('first_confirm_payment/<int:obj_id>/', views.FirstConfirmPayment.as_view(), name='first_confirm'),
    path('secoend_confirm_payment/<int:obj_id>/', views.SecondConfirmPayment.as_view(), name='second_confirm'),
    path('deny_payment/<int:obj_id>/', views.DenyPaymentPage.as_view(), name='deny_payments'),
]