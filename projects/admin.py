from django.contrib import admin

from .models import Entry, Experiment, Project


class ExperimentInline(admin.TabularInline):
    model = Experiment
    extra = 0
    fields = ("order", "slug", "title", "script", "figure", "active")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "track", "difficulty", "status", "lead", "workspace")
    list_filter = ("track", "difficulty", "status")
    search_fields = ("title", "summary", "tools")
    filter_horizontal = ("builds_on", "members")
    inlines = [ExperimentInline]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("project", "kind", "author", "created")
    list_filter = ("kind", "project")
