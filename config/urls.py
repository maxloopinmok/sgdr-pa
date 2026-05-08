from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.events.urls")),
    path("", include("apps.companies.urls")),
    path("", include("apps.core.urls")),
]
