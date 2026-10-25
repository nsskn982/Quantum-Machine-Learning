from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from learning.views import signup

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/signup/", signup, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("projects/", include("projects.urls")),
    path("", include("core.urls")),
    path("", include("learning.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
