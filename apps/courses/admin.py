from django.contrib import admin
from .models import Lessons


@admin.register(Lessons)
class LessonsAdmin(admin.ModelAdmin):
    """Lessons admin configuration."""
    list_display = ('title', 'teacher_names', 'get_homework_count', 'created_at')
    list_filter = ('created_at', 'updated_at', 'teachers')
    search_fields = ('title', 'description', 'teachers__first_name', 'teachers__last_name')
    filter_horizontal = ('teachers',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
        ('Content', {
            'fields': ('content', 'video_url')
        }),
        ('Teachers', {
            'fields': ('teachers',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_homework_count(self, obj):
        """Display homework count in admin list."""
        return obj.get_homework_count()
    get_homework_count.short_description = 'Homework Count'
