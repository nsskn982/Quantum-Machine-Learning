from django.contrib import admin

from .models import Run, RunFigure


class RunFigureInline(admin.TabularInline):
    model = RunFigure
    extra = 0
    readonly_fields = ("name", "file", "primary")


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = ("pk", "target", "user", "status", "error_kind", "created", "duration")
    list_filter = ("status", "error_kind")
    readonly_fields = ("created", "started", "finished", "params", "metrics")
    inlines = [RunFigureInline]
