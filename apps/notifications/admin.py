from django.contrib import admin
from .models import Notification, NotificationPreference, PaymentNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model"""

    list_display = [
        "title",
        "notification_type",
        "recipient_role",
        "recipient",
        "priority",
        "is_read",
        "created_at",
    ]
    list_filter = [
        "notification_type",
        "recipient_role",
        "priority",
        "is_read",
        "created_at",
    ]
    search_fields = ["title", "message", "recipient__username"]
    readonly_fields = ["created_at", "updated_at", "read_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "message", "notification_type", "priority")},
        ),
        ("Recipients", {"fields": ("recipient_role", "recipient")}),
        ("Status", {"fields": ("is_read", "read_at", "is_sent")}),
        (
            "Related Object",
            {"fields": ("content_type", "object_id"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("recipient", "content_type")


@admin.register(PaymentNotification)
class PaymentNotificationAdmin(admin.ModelAdmin):
    """Admin interface for PaymentNotification model"""

    list_display = [
        "payment_reference",
        "payment_type",
        "payment_status",
        "amount",
        "currency",
        "student",
        "teacher",
        "created_at",
    ]
    list_filter = ["payment_type", "payment_status", "currency", "created_at"]
    search_fields = [
        "payment_reference",
        "student__first_name",
        "student__last_name",
        "teacher__first_name",
        "teacher__last_name",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Payment Information",
            {
                "fields": (
                    "payment_reference",
                    "payment_type",
                    "payment_status",
                    "amount",
                    "currency",
                )
            },
        ),
        ("Related Entities", {"fields": ("student", "teacher")}),
        ("Dates", {"fields": ("due_date", "paid_at")}),
        ("Notification", {"fields": ("notification",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return (
            super()
            .get_queryset(request)
            .select_related("notification", "student", "teacher")
        )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for NotificationPreference model"""

    list_display = [
        "user",
        "email_notifications",
        "push_notifications",
        "assignment_notifications",
        "payment_notifications",
        "digest_frequency",
        "updated_at",
    ]
    list_filter = [
        "email_notifications",
        "push_notifications",
        "digest_frequency",
        "payment_notifications",
        "updated_at",
    ]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "General Preferences",
            {
                "fields": (
                    "email_notifications",
                    "push_notifications",
                    "digest_frequency",
                )
            },
        ),
        (
            "Notification Types",
            {
                "fields": (
                    "assignment_notifications",
                    "submission_notifications",
                    "progress_notifications",
                    "schedule_notifications",
                )
            },
        ),
        (
            "Payment Notifications (Admin Only)",
            {
                "fields": (
                    "payment_notifications",
                    "student_payment_notifications",
                    "teacher_payment_notifications",
                ),
                "description": "These settings only apply to admin users",
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("user")
