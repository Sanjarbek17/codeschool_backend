from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class Payment(models.Model):
    """
    Payment model for tracking monthly student payments.
    Each record represents a payment due for a specific student
    for a specific month and group/course.
    """

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        help_text="The student who needs to make this payment",
    )
    group = models.ForeignKey(
        "accounts.Group",
        on_delete=models.CASCADE,
        related_name="payments",
        help_text="The group for which this payment is due",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
        help_text="The course for which this payment is due (optional, derived from group)",
    )

    # Payment details
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Amount due for this month"
    )
    due_date = models.DateField(help_text="Date when payment is due")
    paid_date = models.DateTimeField(
        null=True, blank=True, help_text="Date and time when payment was made"
    )

    # Payment period tracking
    month = models.PositiveIntegerField(
        help_text="Month for which payment is due (1-12)"
    )
    year = models.PositiveIntegerField(help_text="Year for which payment is due")

    status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
        help_text="Current status of the payment",
    )

    # Additional fields
    notes = models.TextField(
        blank=True, help_text="Additional notes about this payment"
    )
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Method used for payment (cash, card, transfer, etc.)",
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payments",
        help_text="Admin user who processed this payment",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_panel_payment"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-year", "-month", "due_date", "student__first_name"]
        unique_together = ["student", "group", "month", "year"]
        indexes = [
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["month", "year"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.group.name} - {self.month}/{self.year} - {self.status}"

    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        return (
            self.status in ["pending", "overdue"]
            and self.due_date < timezone.now().date()
        )

    @property
    def payment_period(self):
        """Return formatted payment period"""
        return f"{self.month:02d}/{self.year}"

    @property
    def days_overdue(self):
        """Return number of days overdue (0 if not overdue)"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0

    def mark_as_paid(self, payment_method="", processed_by=None, notes=""):
        """Mark payment as paid and update related fields"""
        self.status = "paid"
        self.paid_date = timezone.now()
        self.payment_method = payment_method
        self.processed_by = processed_by
        if notes:
            self.notes = notes
        self.save()

    def mark_as_overdue(self):
        """Mark payment as overdue"""
        if self.status == "pending" and self.is_overdue:
            self.status = "overdue"
            self.save()

    @classmethod
    def create_monthly_payments(cls, month, year, default_amount=Decimal("100.00")):
        """
        Create payment records for all active students for a given month/year.
        This should be called at the beginning of each month.
        """
        from apps.accounts.models import Student, Group
        from datetime import date
        import calendar

        created_payments = []

        # Get the last day of the month for due date
        last_day = calendar.monthrange(year, month)[1]
        due_date = date(
            year, month, min(15, last_day)
        )  # Due on 15th or last day if month < 15 days

        # Get all active students with groups
        students_with_groups = (
            Student.objects.filter(groups__isnull=False)
            .prefetch_related("groups", "groups__current_course")
            .distinct()
        )

        for student in students_with_groups:
            for group in student.groups.all():
                # Check if payment already exists for this student/group/month/year
                if not cls.objects.filter(
                    student=student.user, group=group, month=month, year=year
                ).exists():
                    payment = cls.objects.create(
                        student=student.user,
                        group=group,
                        course=group.current_course,
                        amount=default_amount,
                        due_date=due_date,
                        month=month,
                        year=year,
                        status="pending",
                    )
                    created_payments.append(payment)

        return created_payments

    @classmethod
    def update_overdue_payments(cls):
        """
        Update all pending payments that are past due date to overdue status.
        This should be run daily.
        """
        today = timezone.now().date()
        overdue_payments = cls.objects.filter(status="pending", due_date__lt=today)

        updated_count = overdue_payments.update(status="overdue")
        return updated_count

    @classmethod
    def get_student_payment_summary(cls, student_user):
        """Get payment summary for a specific student"""
        from django.db.models import Count, Sum, Q

        payments = cls.objects.filter(student=student_user)

        summary = payments.aggregate(
            total_payments=Count("id"),
            total_amount_due=Sum("amount"),
            paid_count=Count("id", filter=Q(status="paid")),
            pending_count=Count("id", filter=Q(status="pending")),
            overdue_count=Count("id", filter=Q(status="overdue")),
            total_paid_amount=Sum("amount", filter=Q(status="paid")),
        )

        summary["outstanding_amount"] = (summary["total_amount_due"] or 0) - (
            summary["total_paid_amount"] or 0
        )

        return summary
