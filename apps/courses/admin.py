from django.contrib import admin
from .models import Lessons, Attendance


@admin.register(Lessons)
class LessonsAdmin(admin.ModelAdmin):
    """Lessons admin configuration."""

    list_display = ("title", "teacher_names", "get_homework_count", "created_at")
    list_filter = ("created_at", "updated_at", "teachers")
    search_fields = (
        "title",
        "description",
        "teachers__first_name",
        "teachers__last_name",
    )
    filter_horizontal = ("teachers",)
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description")}),
        ("Content", {"fields": ("content", "video_url")}),
        ("Teachers", {"fields": ("teachers",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    def get_homework_count(self, obj):
        """Display homework count in admin list."""
        return obj.get_homework_count()

    get_homework_count.short_description = "Homework Count"


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Attendance admin configuration."""

    list_display = (
        "student",
        "lesson",
        "group",
        "teacher",
        "status",
        "date",
        "created_at",
    )
    list_filter = ("status", "date", "group", "teacher", "created_at")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "lesson__title",
        "group__name",
        "teacher__first_name",
        "teacher__last_name",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-created_at")

    fieldsets = (
        (
            "Attendance Information",
            {"fields": ("student", "lesson", "group", "teacher", "status", "date")},
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("student__user", "lesson", "group", "teacher__user")
        )
