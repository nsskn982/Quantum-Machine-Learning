from django.urls import path

from . import views

urlpatterns = [
    path("runs/<int:pk>/", views.run_detail, name="run_detail"),
]
