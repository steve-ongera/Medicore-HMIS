"""MediCore HMS - Main URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "MediCore HMS Admin"
admin.site.site_title = "MediCore HMS"
admin.site.index_title = "Hospital Management System"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)