from django.contrib import admin

from .models import Module, Progress


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "week", "tool", "script")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "module", "status", "updated")
    list_filter = ("status", "module")
