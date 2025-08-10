from django.contrib import admin
from .models import Homework, Task


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    """Homework admin configuration."""
    list_display = ('title', 'lesson', 'get_task_count', 'created_at')
    list_filter = ('created_at', 'lesson')
    search_fields = ('title', 'description', 'lesson__title')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('lesson', 'title', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_task_count(self, obj):
        """Display task count in admin list."""
        return obj.get_task_count()
    get_task_count.short_description = 'Task Count'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Task admin configuration."""
    list_display = ('title', 'homework', 'get_test_case_count', 'get_submission_count', 'created_at')
    list_filter = ('created_at', 'homework__lesson')
    search_fields = ('title', 'description', 'homework__title')
    ordering = ('homework', '-created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('homework', 'title', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_test_case_count(self, obj):
        """Display test case count in admin list."""
        return obj.get_test_case_count()
    get_test_case_count.short_description = 'Test Cases'
    
    def get_submission_count(self, obj):
        """Display submission count in admin list."""
        return obj.get_submission_count()
    get_submission_count.short_description = 'Submissions'
