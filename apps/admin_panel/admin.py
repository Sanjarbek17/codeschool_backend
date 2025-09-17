from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model"""

    list_display = [
        "student_name",
        "group",
        "payment_period",
        "amount",
        "status",
        "due_date",
        "paid_date",
        "days_overdue_display",
    ]
    list_filter = [
        "status",
        "year",
        "month",
        "group",
        "payment_method",
        "due_date",
        "paid_date",
    ]
    search_fields = [
        "student__username",
        "student__first_name",
        "student__last_name",
        "group__name",
        "notes",
    ]
    readonly_fields = ["created_at", "updated_at", "days_overdue_display"]

    fieldsets = (
        ("Payment Information", {"fields": ("student", "group", "course", "amount")}),
        ("Payment Period", {"fields": ("month", "year", "due_date")}),
        (
            "Payment Status",
            {"fields": ("status", "paid_date", "payment_method", "processed_by")},
        ),
        ("Additional Information", {"fields": ("notes",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def student_name(self, obj):
        """Display student's full name"""
        return obj.student.get_full_name() or obj.student.username

    student_name.short_description = "Student"
    student_name.admin_order_field = "student__first_name"

    def days_overdue_display(self, obj):
        """Display days overdue with styling"""
        days = obj.days_overdue
        if days > 0:
            return f"{days} days"
        return "Not overdue"

    days_overdue_display.short_description = "Days Overdue"

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return (
            super()
            .get_queryset(request)
            .select_related("student", "group", "course", "processed_by")
        )

    actions = ["mark_as_paid", "mark_as_overdue"]

    def mark_as_paid(self, request, queryset):
        """Admin action to mark selected payments as paid"""
        updated = 0
        for payment in queryset.filter(status__in=["pending", "overdue"]):
            payment.mark_as_paid(processed_by=request.user)
            updated += 1

        self.message_user(request, f"Successfully marked {updated} payments as paid.")

    mark_as_paid.short_description = "Mark selected payments as paid"

    def mark_as_overdue(self, request, queryset):
        """Admin action to mark selected payments as overdue"""
        updated = queryset.filter(status="pending").update(status="overdue")
        self.message_user(
            request, f"Successfully marked {updated} payments as overdue."
        )

    mark_as_overdue.short_description = "Mark selected payments as overdue"
