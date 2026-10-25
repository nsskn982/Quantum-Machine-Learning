from django.urls import path

from . import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("new/", views.project_create, name="project_create"),
    path("<slug:slug>/", views.project_detail, name="project_detail"),
    path("<slug:slug>/join/", views.project_join, name="project_join"),
    path("<slug:slug>/leave/", views.project_leave, name="project_leave"),
    path("<slug:slug>/settings/", views.project_settings, name="project_settings"),
    path("<slug:slug>/journal/", views.entry_create, name="entry_create"),
    path("<slug:slug>/experiments/<slug:exp>/run/", views.experiment_run, name="experiment_run"),
    path("<slug:slug>/experiments/<slug:exp>/script/", views.experiment_script, name="experiment_script"),
]
