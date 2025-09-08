from django.contrib import admin
from .models import HomeworkSubmission, TestCase


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    """HomeworkSubmission admin configuration."""

    list_display = (
        "id",
        "student",
        "task",
        "passed_tests",
        "total_tests",
        "success_rate",
        "is_successful",
        "submitted_at",
    )
    list_filter = ("submitted_at", "task__homework__lesson")
    search_fields = ("student__first_name", "student__last_name", "task__title")
    ordering = ("-submitted_at",)

    fieldsets = (
        (
            "Submission Information",
            {"fields": ("task", "student", "code_text", "file_upload")},
        ),
        (
            "Test Results",
            {
                "fields": (
                    "passed_tests",
                    "total_tests",
                    "execution_time",
                    "memory_usage",
                )
            },
        ),
        ("Metadata", {"fields": ("submitted_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ("submitted_at", "success_rate", "is_successful")

    def success_rate(self, obj):
        """Display success rate in admin."""
        return f"{obj.success_rate:.1f}%"

    success_rate.short_description = "Success Rate"

    def is_successful(self, obj):
        """Display success status in admin."""
        return obj.is_successful

    is_successful.boolean = True
    is_successful.short_description = "Successful"


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    """TestCase admin configuration."""

    list_display = (
        "id",
        "task",
        "get_task_id",
        "hidden",
        "timeout_seconds",
        "created_at",
    )
    list_filter = ("hidden", "task__homework__lesson", "created_at")
    search_fields = ("task__title", "test_code", "input_data", "expected_output")
    ordering = ("task", "hidden", "-created_at")

    fieldsets = (
        (
            "Test Information",
            {"fields": ("task", "test_code", "hidden", "timeout_seconds")},
        ),
        (
            "Test Data",
            {"fields": ("input_data", "expected_output"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    def get_task_id(self, obj):
        """Display task ID in admin list."""
        return obj.task.id if obj.task else None

    get_task_id.short_description = "Task ID"
