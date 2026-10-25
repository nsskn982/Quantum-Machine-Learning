from django.conf import settings

from .services import can_run_scripts


def portal_flags(request):
    return {
        "signup_enabled": settings.QML_SIGNUP_ENABLED,
        "can_run": can_run_scripts(getattr(request, "user", None)),
    }
