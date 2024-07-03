from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path('confirm_payment/<int:show_box>/', views.ConfirmPaymentPage.as_view(), name='confirm_payments'),
    path('first_confirm_payment/<int:obj_id>/', views.FirstConfirmPayment.as_view(), name='first_confirm'),
    path('secoend_confirm_payment/<int:obj_id>/', views.SecondConfirmPayment.as_view(), name='second_confirm'),
    path('first_tamdid_confirm_payment/<int:obj_id>/', views.FirstTamdidConfirmPayment.as_view(), name='first_tamdid_confirm'),
    path('secoend_tamdid_confirm_payment/<int:obj_id>/', views.SecondTamdidConfirmPayment.as_view(), name='second_tamdid_confirm'),

    path('deny_tamdid_payment_after_first_confirm/<int:obj_id>/', views.DenyTamdidPaymentAfterFirsConfirmPage.as_view(),
         name='deny_tamdid_payments_after_first_confirm'),
    path('deny_payment_after_first_confirm/<int:obj_id>/', views.DenyPaymentAfterFirsConfirmPage.as_view(), name='deny_payments_after_first_confirm'),
    path('deny_payment/<int:obj_id>/<str:typ>/', views.DenyPaymentPage.as_view(), name='deny_payments'),
    path('edit_price_payment/<int:obj_id>/<str:typ>/', views.EditPricePayment.as_view(), name='edit_price'),
    path("paid_after_create/<int:obj_id>/", views.PayedAfterCreate.as_view(), name="paid_after_create"),


    path('show_prices/', views.ShowPrices.as_view(), name='show_prices'),
    path('delete_or_edit_price/<int:obj_id>/<str:action>/', views.DeleteOrEditPrice.as_view(), name='delete_or_edit_price'),
    path('add_price/', views.AddPrice.as_view(), name='add_price'),
]