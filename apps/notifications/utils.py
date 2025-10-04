from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, Count
from .models import Notification, NotificationPreference, PaymentNotification
import uuid

User = get_user_model()


def create_notification(
    title,
    message,
    notification_type,
    recipient_role="all",
    recipient=None,
    priority="medium",
    related_object=None,
):
    """
    Create a new notification with proper role validation.

    Args:
        title: Notification title
        message: Notification message
        notification_type: Type from Notification.NOTIFICATION_TYPES
        recipient_role: Target role from Notification.RECIPIENT_ROLES
        recipient: Specific user (optional)
        priority: Priority level
        related_object: Related model instance (optional)

    Returns:
        Notification instance
    """
    # Validate payment notifications
    if notification_type in ["payment", "student_payment", "teacher_payment"]:
        if recipient_role != "admin":
            raise ValueError("Payment notifications can only be sent to admin users.")

    # Set up generic foreign key if related object provided
    content_type = None
    object_id = None
    if related_object:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = related_object.pk

    notification = Notification.objects.create(
        title=title,
        message=message,
        notification_type=notification_type,
        recipient_role=recipient_role,
        recipient=recipient,
        priority=priority,
        content_type=content_type,
        object_id=object_id,
    )

    return notification


def create_payment_notification(
    title,
    message,
    payment_type,
    payment_status,
    amount,
    currency="USD",
    student=None,
    teacher=None,
    due_date=None,
    payment_reference=None,
):
    """
    Create a payment notification (admin only).

    Args:
        title: Notification title
        message: Notification message
        payment_type: Type from PaymentNotification.PAYMENT_TYPES
        payment_status: Status from PaymentNotification.PAYMENT_STATUS
        amount: Payment amount
        currency: Payment currency
        student: Related student (for tuition payments)
        teacher: Related teacher (for salary payments)
        due_date: Payment due date
        payment_reference: Unique payment reference

    Returns:
        PaymentNotification instance
    """
    # Generate unique payment reference if not provided
    if not payment_reference:
        payment_reference = f"PAY-{uuid.uuid4().hex[:8].upper()}"

    # Determine notification type based on payment type
    if payment_type in ["tuition", "penalty"]:
        notification_type = "student_payment"
    elif payment_type in ["salary", "bonus"]:
        notification_type = "teacher_payment"
    else:
        notification_type = "payment"

    # Create the base notification
    notification = create_notification(
        title=title,
        message=message,
        notification_type=notification_type,
        recipient_role="admin",
        priority="high" if payment_status in ["failed", "overdue"] else "medium",
    )

    # Create the payment notification details
    payment_notification = PaymentNotification.objects.create(
        notification=notification,
        payment_type=payment_type,
        payment_status=payment_status,
        amount=amount,
        currency=currency,
        student=student,
        teacher=teacher,
        payment_reference=payment_reference,
        due_date=due_date,
    )

    return payment_notification


def get_user_notifications(user, unread_only=False, notification_type=None):
    """
    Get notifications for a specific user based on their role.

    Args:
        user: User instance
        unread_only: Return only unread notifications
        notification_type: Filter by notification type

    Returns:
        QuerySet of Notification objects
    """
    user_role = Notification.get_user_role(user)

    # Base query - notifications for user's role or specifically for this user
    notifications = Notification.objects.filter(
        Q(recipient_role=user_role) | Q(recipient_role="all") | Q(recipient=user)
    )

    # Filter out payment notifications for non-admin users
    if user_role != "admin":
        notifications = notifications.exclude(
            notification_type__in=["payment", "student_payment", "teacher_payment"]
        )

    # Apply filters
    if unread_only:
        notifications = notifications.filter(is_read=False)

    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)

    return notifications


def bulk_mark_as_read(user, notification_ids=None):
    """
    Mark multiple notifications as read for a user.

    Args:
        user: User instance
        notification_ids: List of notification IDs (optional, marks all if None)

    Returns:
        Number of notifications marked as read
    """
    from django.utils import timezone

    notifications = get_user_notifications(user, unread_only=True)

    if notification_ids:
        notifications = notifications.filter(id__in=notification_ids)

    count = notifications.update(is_read=True, read_at=timezone.now())

    return count


def get_notification_stats(user):
    """
    Get notification statistics for a user.

    Args:
        user: User instance

    Returns:
        Dict with notification statistics
    """
    notifications = get_user_notifications(user)

    total = notifications.count()
    unread = notifications.filter(is_read=False).count()
    by_type = (
        notifications.values("notification_type")
        .annotate(count=Count("id"))
        .order_by("notification_type")
    )
    by_priority = (
        notifications.filter(is_read=False)
        .values("priority")
        .annotate(count=Count("id"))
        .order_by("priority")
    )

    return {
        "total": total,
        "unread": unread,
        "read": total - unread,
        "by_type": list(by_type),
        "by_priority": list(by_priority),
    }


def create_bulk_notifications(
    title,
    message,
    notification_type,
    recipient_role,
    recipients=None,
    priority="medium",
    related_object=None,
):
    """
    Create bulk notifications for multiple recipients or role-based targeting.

    Args:
        title: Notification title
        message: Notification message
        notification_type: Type from Notification.NOTIFICATION_TYPES
        recipient_role: Target role from Notification.RECIPIENT_ROLES
        recipients: List of specific users (optional)
        priority: Priority level
        related_object: Related model instance (optional)

    Returns:
        List of created Notification instances
    """
    notifications = []

    # Set up generic foreign key if related object provided
    content_type = None
    object_id = None
    if related_object:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = related_object.pk

    if recipients:
        # Create notifications for specific recipients
        for recipient in recipients:
            notification = Notification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type,
                recipient_role=recipient_role,
                recipient=recipient,
                priority=priority,
                content_type=content_type,
                object_id=object_id,
            )
            notifications.append(notification)
    else:
        # Create a single notification for the role
        notification = Notification.objects.create(
            title=title,
            message=message,
            notification_type=notification_type,
            recipient_role=recipient_role,
            priority=priority,
            content_type=content_type,
            object_id=object_id,
        )
        notifications.append(notification)

    return notifications


def get_or_create_user_preferences(user):
    """
    Get or create notification preferences for a user.

    Args:
        user: User instance

    Returns:
        NotificationPreference instance
    """
    preferences, created = NotificationPreference.objects.get_or_create(
        user=user,
        defaults={
            "email_notifications": True,
            "push_notifications": True,
            "assignment_notifications": True,
            "submission_notifications": True,
            "progress_notifications": True,
            "schedule_notifications": True,
            "payment_notifications": Notification.get_user_role(user) == "admin",
            "student_payment_notifications": Notification.get_user_role(user)
            == "admin",
            "teacher_payment_notifications": Notification.get_user_role(user)
            == "admin",
            "digest_frequency": "immediate",
        },
    )

    return preferences
