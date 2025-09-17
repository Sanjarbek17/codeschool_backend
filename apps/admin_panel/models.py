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
        ("partially_paid", "Partially Paid"),
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
        max_digits=10, decimal_places=2, help_text="Total amount due for this month"
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Amount that has been paid so far",
    )
    due_date = models.DateField(help_text="Date when payment is due")
    paid_date = models.DateTimeField(
        null=True, blank=True, help_text="Date and time when payment was fully paid"
    )

    # Payment period tracking
    month = models.PositiveIntegerField(
        help_text="Month for which payment is due (1-12)"
    )
    year = models.PositiveIntegerField(help_text="Year for which payment is due")

    status = models.CharField(
        max_length=15,
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
            self.status in ["pending", "overdue", "partially_paid"]
            and self.due_date < timezone.now().date()
        )

    @property
    def remaining_amount(self):
        """Calculate remaining amount to be paid"""
        return self.amount - self.paid_amount

    @property
    def payment_percentage(self):
        """Calculate percentage of payment completed"""
        if self.amount > 0:
            return (self.paid_amount / self.amount) * 100
        return 0

    @property
    def is_fully_paid(self):
        """Check if payment is fully paid"""
        return self.paid_amount >= self.amount

    @property
    def is_partially_paid(self):
        """Check if payment is partially paid"""
        return self.paid_amount > 0 and self.paid_amount < self.amount

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

    def add_payment(self, amount, payment_method="", processed_by=None, notes=""):
        """Add a partial payment to this payment record"""
        if amount <= 0:
            raise ValueError("Payment amount must be positive")

        if self.paid_amount + amount > self.amount:
            raise ValueError("Payment amount exceeds remaining balance")

        self.paid_amount += amount
        self.payment_method = payment_method
        self.processed_by = processed_by

        if notes:
            if self.notes:
                self.notes += f"\n{notes}"
            else:
                self.notes = notes

        # Update status based on payment completion
        if self.is_fully_paid:
            self.status = "paid"
            self.paid_date = timezone.now()
        elif self.is_partially_paid:
            self.status = "partially_paid"

        self.save()
        return self.remaining_amount

    def mark_as_paid(self, payment_method="", processed_by=None, notes=""):
        """Mark payment as fully paid"""
        self.paid_amount = self.amount
        self.status = "paid"
        self.paid_date = timezone.now()
        self.payment_method = payment_method
        self.processed_by = processed_by
        if notes:
            self.notes = notes
        self.save()

    def mark_as_overdue(self):
        """Mark payment as overdue"""
        if self.status in ["pending", "partially_paid"] and self.is_overdue:
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
        Update all pending and partially paid payments that are past due date to overdue status.
        This should be run daily.
        """
        today = timezone.now().date()
        overdue_payments = cls.objects.filter(
            status__in=["pending", "partially_paid"], due_date__lt=today
        )

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
            partially_paid_count=Count("id", filter=Q(status="partially_paid")),
            overdue_count=Count("id", filter=Q(status="overdue")),
            total_paid_amount=Sum("paid_amount"),
        )

        summary["outstanding_amount"] = (summary["total_amount_due"] or 0) - (
            summary["total_paid_amount"] or 0
        )

        return summary

    @classmethod
    def get_student_unpaid_months(cls, student_user):
        """Get number of consecutive unpaid months for a student"""
        from django.utils import timezone
        from datetime import date

        today = timezone.now().date()
        current_month = today.month
        current_year = today.year

        unpaid_months = 0
        month, year = current_month, current_year

        # Go back month by month counting unpaid payments
        for _ in range(12):  # Check up to 12 months back
            unpaid_payments = cls.objects.filter(
                student=student_user,
                month=month,
                year=year,
                status__in=["pending", "overdue", "partially_paid"],
            )

            if unpaid_payments.exists():
                unpaid_months += 1
            else:
                break  # Stop when we find a paid month

            # Go to previous month
            month -= 1
            if month == 0:
                month = 12
                year -= 1

        return unpaid_months

    @classmethod
    def get_students_with_multiple_unpaid_months(cls, min_months=2):
        """Get students who haven't paid for multiple months"""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        students_at_risk = []

        # Get all students with payments
        students = User.objects.filter(payments__isnull=False).distinct()

        for student in students:
            unpaid_months = cls.get_student_unpaid_months(student)
            if unpaid_months >= min_months:
                total_debt = (
                    cls.objects.filter(
                        student=student,
                        status__in=["pending", "overdue", "partially_paid"],
                    ).aggregate(
                        total_debt=models.Sum(
                            models.F("amount") - models.F("paid_amount")
                        )
                    )[
                        "total_debt"
                    ]
                    or 0
                )

                students_at_risk.append(
                    {
                        "student": student,
                        "unpaid_months": unpaid_months,
                        "total_debt": total_debt,
                    }
                )

        return students_at_risk

    def should_suspend_student(self):
        """Check if student should be suspended based on payment history"""
        unpaid_months = self.__class__.get_student_unpaid_months(self.student)
        return unpaid_months >= 3  # Suspend after 3 months of non-payment

    @classmethod
    def get_suspension_candidates(cls):
        """Get students who should be suspended due to non-payment"""
        return cls.get_students_with_multiple_unpaid_months(min_months=3)


# Add a new model for tracking student payment status
class StudentPaymentStatus(models.Model):
    """
    Model to track overall payment status and restrictions for students
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("warning", "Payment Warning"),
        ("suspended", "Suspended for Non-Payment"),
        ("expelled", "Expelled"),
    ]

    student = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="payment_status",
        help_text="Student user account",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Current payment status of the student",
    )
    consecutive_unpaid_months = models.PositiveIntegerField(
        default=0, help_text="Number of consecutive months without payment"
    )
    total_debt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total amount owed across all unpaid payments",
    )
    last_payment_date = models.DateField(
        null=True, blank=True, help_text="Date of last payment made"
    )
    suspension_date = models.DateField(
        null=True, blank=True, help_text="Date when student was suspended"
    )
    warning_sent_date = models.DateField(
        null=True, blank=True, help_text="Date when last warning was sent"
    )
    notes = models.TextField(
        blank=True, help_text="Additional notes about payment status"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_panel_student_payment_status"
        verbose_name = "Student Payment Status"
        verbose_name_plural = "Student Payment Statuses"
        ordering = ["-consecutive_unpaid_months", "-total_debt"]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.status} - {self.consecutive_unpaid_months} months"

    def update_status(self):
        """Update student status based on payment history"""
        unpaid_months = Payment.get_student_unpaid_months(self.student)

        # Calculate total debt
        total_debt = Payment.objects.filter(
            student=self.student, status__in=["pending", "overdue", "partially_paid"]
        ).aggregate(debt=models.Sum(models.F("amount") - models.F("paid_amount")))[
            "debt"
        ] or Decimal(
            "0.00"
        )

        # Get last payment date
        last_payment = (
            Payment.objects.filter(student=self.student, status="paid")
            .order_by("-paid_date")
            .first()
        )

        self.consecutive_unpaid_months = unpaid_months
        self.total_debt = total_debt
        self.last_payment_date = last_payment.paid_date.date() if last_payment else None

        # Update status based on unpaid months
        if unpaid_months >= 4:
            self.status = "expelled"
        elif unpaid_months >= 3:
            if self.status != "suspended":
                self.suspension_date = timezone.now().date()
            self.status = "suspended"
        elif unpaid_months >= 2:
            self.status = "warning"
            if (
                not self.warning_sent_date
                or (timezone.now().date() - self.warning_sent_date).days > 30
            ):
                self.warning_sent_date = timezone.now().date()
        else:
            self.status = "active"
            self.suspension_date = None
            self.warning_sent_date = None

        self.save()
        return self.status

    @classmethod
    def update_all_statuses(cls):
        """Update payment status for all students"""
        from apps.accounts.models import Student

        updated_count = 0
        for student_profile in Student.objects.all():
            status, created = cls.objects.get_or_create(student=student_profile.user)
            old_status = status.status
            new_status = status.update_status()

            if old_status != new_status:
                updated_count += 1

        return updated_count

        return summary
