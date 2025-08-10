from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Teacher, Student


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin configuration."""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Teacher admin configuration."""
    list_display = ('full_name', 'phone_number', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('first_name', 'last_name', 'user__username', 'phone_number')
    ordering = ('last_name', 'first_name')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'first_name', 'last_name', 'phone_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Student admin configuration."""
    list_display = ('full_name', 'phone_number', 'parents_phone_number', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('first_name', 'last_name', 'user__username', 'phone_number', 'parents_phone_number')
    ordering = ('last_name', 'first_name')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'first_name', 'last_name', 'phone_number', 'parents_phone_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
