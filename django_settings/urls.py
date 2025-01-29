from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("grappelli/", include("grappelli.urls")),  # grappelli URLS
    path("admin/", admin.site.urls, name="admin"),
    path("", include("eshop_app.urls")),
]
