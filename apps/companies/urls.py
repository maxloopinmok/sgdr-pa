from django.urls import path

from . import views

urlpatterns = [
    path("companies/", views.companies_list, name="companies_list"),
    path("companies/<str:ticker>/", views.company_timeline, name="company_timeline"),
]
