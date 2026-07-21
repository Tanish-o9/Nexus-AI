from django.contrib import admin
from .models import Sprint, SprintBacklogItem, SprintReport


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'start_date', 'end_date', 'is_active', 'is_completed')
    list_filter = ('is_active', 'is_completed')


@admin.register(SprintBacklogItem)
class SprintBacklogItemAdmin(admin.ModelAdmin):
    list_display = ('sprint', 'task', 'story_points')


@admin.register(SprintReport)
class SprintReportAdmin(admin.ModelAdmin):
    list_display = ('sprint', 'report_type', 'created_at')
    list_filter = ('report_type',)