from django.contrib import admin
from django.utils import timezone
from .models import Payment, StudentPaymentStatus


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model"""

    list_display = [
        "student_name",
        "group",
        "payment_period",
        "amount",
        "paid_amount",
        "remaining_amount_display",
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
        (
            "Payment Information",
            {"fields": ("student", "group", "course", "amount", "paid_amount")},
        ),
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

    def remaining_amount_display(self, obj):
        """Display remaining amount"""
        return obj.remaining_amount

    remaining_amount_display.short_description = "Remaining"
    remaining_amount_display.admin_order_field = "amount"

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
        for payment in queryset.filter(
            status__in=["pending", "overdue", "partially_paid"]
        ):
            payment.mark_as_paid(processed_by=request.user)
            updated += 1

        self.message_user(request, f"Successfully marked {updated} payments as paid.")

    mark_as_paid.short_description = "Mark selected payments as paid"

    def mark_as_overdue(self, request, queryset):
        """Admin action to mark selected payments as overdue"""
        updated = queryset.filter(status__in=["pending", "partially_paid"]).update(
            status="overdue"
        )
        self.message_user(
            request, f"Successfully marked {updated} payments as overdue."
        )

    mark_as_overdue.short_description = "Mark selected payments as overdue"


@admin.register(StudentPaymentStatus)
class StudentPaymentStatusAdmin(admin.ModelAdmin):
    """Admin interface for StudentPaymentStatus model"""

    list_display = [
        "student_name",
        "status",
        "consecutive_unpaid_months",
        "total_debt",
        "last_payment_date",
        "suspension_date",
    ]
    list_filter = [
        "status",
        "consecutive_unpaid_months",
        "suspension_date",
        "warning_sent_date",
        "created_at",
    ]
    search_fields = ["student__username", "student__first_name", "student__last_name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Student Information", {"fields": ("student",)}),
        (
            "Payment Status",
            {"fields": ("status", "consecutive_unpaid_months", "total_debt")},
        ),
        (
            "Important Dates",
            {"fields": ("last_payment_date", "suspension_date", "warning_sent_date")},
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

    actions = ["update_statuses", "send_warnings", "suspend_students"]

    def update_statuses(self, request, queryset):
        """Update payment status for selected students"""
        updated = 0
        for payment_status in queryset:
            old_status = payment_status.status
            new_status = payment_status.update_status()
            if old_status != new_status:
                updated += 1

        self.message_user(request, f"Updated status for {updated} students")

    update_statuses.short_description = "Update payment statuses"

    def send_warnings(self, request, queryset):
        """Send warnings to students with overdue payments"""
        warned = 0
        for payment_status in queryset.filter(status__in=["warning", "overdue"]):
            payment_status.warning_sent_date = timezone.now().date()
            payment_status.save()
            warned += 1

        self.message_user(request, f"Sent warnings to {warned} students")

    send_warnings.short_description = "Send payment warnings"

    def suspend_students(self, request, queryset):
        """Suspend students with 3+ unpaid months"""
        suspended = 0
        for payment_status in queryset.filter(consecutive_unpaid_months__gte=3):
            if payment_status.status != "suspended":
                payment_status.status = "suspended"
                payment_status.suspension_date = timezone.now().date()
                payment_status.save()
                suspended += 1

        self.message_user(request, f"Suspended {suspended} students for non-payment")

    suspend_students.short_description = "Suspend students for non-payment"
