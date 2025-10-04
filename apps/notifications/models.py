from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError

User = get_user_model()


class Notification(models.Model):
    """
    Notification model for handling various types of notifications with role-based filtering.
    Supports admin-only payments notifications and teacher-specific notifications.
    """

    NOTIFICATION_TYPES = [
        ("assignment", "New Assignment"),
        ("submission", "Submission Graded"),
        ("progress", "Progress Milestone"),
        ("schedule", "Schedule Change"),
        ("announcement", "General Announcement"),
        ("deadline", "Deadline Reminder"),
        ("payment", "Payment Notification"),  # Admin only
        ("student_payment", "Student Payment Status"),  # Admin only
        ("teacher_payment", "Teacher Payment"),  # Admin only
    ]

    RECIPIENT_ROLES = [
        ("admin", "Admin Only"),
        ("teacher", "Teachers Only"),
        ("student", "Students Only"),
        ("all", "All Users"),
    ]

    PRIORITY_LEVELS = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    title = models.CharField(max_length=200, help_text="Notification title")
    message = models.TextField(help_text="Notification message content")
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, help_text="Type of notification"
    )
    recipient_role = models.CharField(
        max_length=10,
        choices=RECIPIENT_ROLES,
        default="all",
        help_text="Target role for this notification",
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        help_text="Specific recipient (optional, for targeted notifications)",
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default="medium",
        help_text="Notification priority level",
    )

    # Generic foreign key for related objects
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey("content_type", "object_id")

    # Notification status
    is_read = models.BooleanField(
        default=False, help_text="Whether notification has been read"
    )
    is_sent = models.BooleanField(
        default=False, help_text="Whether notification has been sent"
    )
    read_at = models.DateTimeField(
        null=True, blank=True, help_text="When notification was read"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notifications_notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at", "-priority"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["notification_type", "recipient_role"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        if self.recipient:
            return f"{self.title} → {self.recipient.username}"
        return f"{self.title} → {self.recipient_role}"

    def clean(self):
        """Validate notification based on type and role restrictions"""
        # Payment notifications should only be for admin
        if self.notification_type in ["payment", "student_payment", "teacher_payment"]:
            if self.recipient_role != "admin":
                raise ValidationError(
                    "Payment notifications can only be sent to admin users."
                )

        # If recipient is specified, validate role
        if self.recipient and self.recipient_role != "all":
            user_role = self.get_user_role(self.recipient)
            if user_role != self.recipient_role:
                raise ValidationError(
                    f"Recipient role mismatch. User is {user_role} but notification is for {self.recipient_role}."
                )

    @staticmethod
    def get_user_role(user):
        """Determine user role based on profile"""
        if user.is_superuser or user.is_staff:
            return "admin"
        elif hasattr(user, "teacher_profile"):
            return "teacher"
        elif hasattr(user, "student_profile"):
            return "student"
        return "admin"  # Default to admin for safety

    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone

        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])

    def get_related_object_info(self):
        """Get information about the related object"""
        if self.related_object:
            return {
                "type": self.content_type.model,
                "id": self.object_id,
                "object": str(self.related_object),
            }
        return None


class NotificationPreference(models.Model):
    """
    User notification preferences for different types of notifications.
    Role-based preferences with admin-specific payment notification settings.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )

    # General preferences
    email_notifications = models.BooleanField(
        default=True, help_text="Receive notifications via email"
    )
    push_notifications = models.BooleanField(
        default=True, help_text="Receive push notifications"
    )

    # Teacher-specific preferences
    assignment_notifications = models.BooleanField(
        default=True, help_text="Receive assignment-related notifications"
    )
    submission_notifications = models.BooleanField(
        default=True, help_text="Receive submission-related notifications"
    )
    progress_notifications = models.BooleanField(
        default=True, help_text="Receive progress-related notifications"
    )
    schedule_notifications = models.BooleanField(
        default=True, help_text="Receive schedule-related notifications"
    )

    # Admin-specific preferences (payment notifications)
    payment_notifications = models.BooleanField(
        default=True, help_text="Receive payment-related notifications (admin only)"
    )
    student_payment_notifications = models.BooleanField(
        default=True, help_text="Receive student payment notifications (admin only)"
    )
    teacher_payment_notifications = models.BooleanField(
        default=True, help_text="Receive teacher payment notifications (admin only)"
    )

    # Frequency settings
    digest_frequency = models.CharField(
        max_length=10,
        choices=[
            ("immediate", "Immediate"),
            ("hourly", "Hourly"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
        ],
        default="immediate",
        help_text="How often to receive notification digests",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notifications_preference"
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Preferences for {self.user.username}"

    def clean(self):
        """Validate preferences based on user role"""
        user_role = Notification.get_user_role(self.user)

        # Only admin users should have payment notification preferences
        if user_role != "admin":
            self.payment_notifications = False
            self.student_payment_notifications = False
            self.teacher_payment_notifications = False


class PaymentNotification(models.Model):
    """
    Specialized model for payment-related notifications (admin only).
    Tracks payment events and notifications.
    """

    PAYMENT_TYPES = [
        ("tuition", "Tuition Payment"),
        ("salary", "Teacher Salary"),
        ("refund", "Refund"),
        ("penalty", "Late Payment Penalty"),
        ("bonus", "Bonus Payment"),
    ]

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("overdue", "Overdue"),
    ]

    notification = models.OneToOneField(
        Notification, on_delete=models.CASCADE, related_name="payment_details"
    )
    payment_type = models.CharField(
        max_length=20, choices=PAYMENT_TYPES, help_text="Type of payment"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, help_text="Status of the payment"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Payment amount"
    )
    currency = models.CharField(
        max_length=3, default="USD", help_text="Payment currency"
    )

    # Related entities
    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Student related to this payment (for tuition)",
    )
    teacher = models.ForeignKey(
        "accounts.Teacher",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Teacher related to this payment (for salary)",
    )

    # Payment metadata
    payment_reference = models.CharField(
        max_length=100, unique=True, help_text="Unique payment reference"
    )
    due_date = models.DateTimeField(null=True, blank=True, help_text="Payment due date")
    paid_at = models.DateTimeField(
        null=True, blank=True, help_text="When payment was completed"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notifications_payment"
        verbose_name = "Payment Notification"
        verbose_name_plural = "Payment Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payment_type} - {self.amount} {self.currency} ({self.payment_status})"

    def clean(self):
        """Validate payment notification"""
        if self.notification.notification_type not in [
            "payment",
            "student_payment",
            "teacher_payment",
        ]:
            raise ValidationError(
                "Payment notification must have payment-related notification type."
            )

        if self.notification.recipient_role != "admin":
            raise ValidationError(
                "Payment notifications can only be sent to admin users."
            )
