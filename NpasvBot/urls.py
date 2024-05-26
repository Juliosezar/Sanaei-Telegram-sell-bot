from django.contrib import admin
from django.urls import path
from connection import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/', views.webhook, name='webhook'),
]
