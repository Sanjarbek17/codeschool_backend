from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Teacher, Student, Group


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin configuration."""

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Teacher admin configuration."""

    list_display = ("full_name", "phone_number", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("first_name", "last_name", "user__username", "phone_number")
    ordering = ("last_name", "first_name")

    fieldsets = (
        (
            "Personal Information",
            {"fields": ("user", "first_name", "last_name", "phone_number")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Student admin configuration."""

    list_display = (
        "full_name",
        "phone_number",
        "parents_phone_number",
        "user",
        "created_at",
    )
    list_filter = ("created_at", "groups")
    search_fields = (
        "first_name",
        "last_name",
        "user__username",
        "phone_number",
        "parents_phone_number",
    )
    filter_horizontal = ("groups",)
    ordering = ("last_name", "first_name")

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "user",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "parents_phone_number",
                )
            },
        ),
        ("Groups", {"fields": ("groups",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Group admin configuration."""

    list_display = (
        "name",
        "teacher_count",
        "student_count",
        "current_course_display",
        "current_lesson_display",
        "created_date",
    )
    list_filter = ("created_date", "teachers", "current_course", "current_lesson")
    search_fields = ("name", "teachers__first_name", "teachers__last_name")
    filter_horizontal = ("teachers",)
    ordering = ("name",)

    fieldsets = (
        ("Basic Information", {"fields": ("name",)}),
        ("Teachers", {"fields": ("teachers",)}),
        (
            "Current Course & Lesson",
            {
                "fields": ("current_course", "current_lesson", "last_taught_date"),
                "description": "Set the current course and lesson being taught in this group",
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_date", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_date", "updated_at", "last_taught_date")

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related and select_related."""
        return (
            super()
            .get_queryset(request)
            .prefetch_related("teachers", "students")
            .select_related("current_course", "current_lesson")
        )

    def current_course_display(self, obj):
        """Display current course title or 'None' if not set."""
        return obj.current_course.title if obj.current_course else "None"

    current_course_display.short_description = "Current Course"

    def current_lesson_display(self, obj):
        """Display current lesson title or 'None' if not set."""
        return obj.current_lesson.title if obj.current_lesson else "None"

    current_lesson_display.short_description = "Current Lesson"
