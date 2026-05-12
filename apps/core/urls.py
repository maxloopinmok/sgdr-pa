from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("commentary/", views.commentary, name="commentary"),
    path("about/", views.about, name="about"),
    path("legal/disclaimer/", views.disclaimer, name="disclaimer"),
    path("healthz", views.healthz, name="healthz"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
]
