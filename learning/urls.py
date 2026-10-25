from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("modules/<slug:slug>/", views.module_detail, name="module_detail"),
    path("modules/<slug:slug>/run/", views.module_run, name="module_run"),
    path("modules/<slug:slug>/script/", views.download_script, name="module_script"),
]
