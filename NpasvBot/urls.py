from django.contrib import admin
from django.urls import path, include
from connection import views
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/', views.webhook, name='webhook'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path(r'', RedirectView.as_view(url='accounts/home/')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('customers/', include('custumers.urls', namespace='customers')),
    path('servers/', include('servers.urls', namespace='servers')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
