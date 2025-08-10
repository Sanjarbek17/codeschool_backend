from django.contrib import admin
from .models import HomeworkProgress, TaskProgress


@admin.register(HomeworkProgress)
class HomeworkProgressAdmin(admin.ModelAdmin):
    """HomeworkProgress admin configuration."""
    list_display = ('student', 'homework', 'solved_tasks', 'total_tasks', 'completion_percentage', 'is_completed', 'last_attempt_at')
    list_filter = ('is_completed', 'homework__lesson', 'last_attempt_at')
    search_fields = ('student__first_name', 'student__last_name', 'homework__title')
    ordering = ('-last_attempt_at',)
    
    fieldsets = (
        ('Progress Information', {
            'fields': ('homework', 'student', 'total_tasks', 'solved_tasks', 'is_completed')
        }),
        ('Timestamps', {
            'fields': ('last_attempt_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'completion_percentage')
    
    def completion_percentage(self, obj):
        """Display completion percentage in admin."""
        return f"{obj.completion_percentage:.1f}%"
    completion_percentage.short_description = 'Completion %'


@admin.register(TaskProgress)
class TaskProgressAdmin(admin.ModelAdmin):
    """TaskProgress admin configuration."""
    list_display = ('student', 'task', 'best_passed_tests', 'total_tests', 'test_pass_percentage', 'is_solved', 'last_attempt_at')
    list_filter = ('is_solved', 'task__homework__lesson', 'last_attempt_at')
    search_fields = ('student__first_name', 'student__last_name', 'task__title')
    ordering = ('-last_attempt_at',)
    
    fieldsets = (
        ('Progress Information', {
            'fields': ('task', 'student', 'is_solved', 'best_passed_tests', 'total_tests', 'last_submission')
        }),
        ('Timestamps', {
            'fields': ('last_attempt_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'test_pass_percentage')
    
    def test_pass_percentage(self, obj):
        """Display test pass percentage in admin."""
        return f"{obj.test_pass_percentage:.1f}%"
    test_pass_percentage.short_description = 'Test Pass %'
