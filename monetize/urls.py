from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path("", include("home.urls")),
]

if settings.DEPLOYMENT == 'local':
    debug_urls = [path('admin/', admin.site.urls)]
    urlpatterns = urlpatterns + debug_urls

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)