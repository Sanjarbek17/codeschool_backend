from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Notification, NotificationPreference, PaymentNotification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model with role-based filtering.
    """

    related_object_info = serializers.SerializerMethodField()
    recipient_username = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    can_view = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "recipient_role",
            "recipient",
            "recipient_username",
            "priority",
            "is_read",
            "read_at",
            "created_at",
            "updated_at",
            "related_object_info",
            "user_role",
            "can_view",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "related_object_info",
            "recipient_username",
            "user_role",
            "can_view",
        ]

    def get_related_object_info(self, obj):
        """Get information about the related object"""
        return obj.get_related_object_info()

    def get_recipient_username(self, obj):
        """Get recipient username if exists"""
        return obj.recipient.username if obj.recipient else None

    def get_user_role(self, obj):
        """Get the user role for context"""
        request = self.context.get("request")
        if request and request.user:
            return Notification.get_user_role(request.user)
        return None

    def get_can_view(self, obj):
        """Check if current user can view this notification"""
        request = self.context.get("request")
        if not request or not request.user:
            return False

        user_role = Notification.get_user_role(request.user)

        # Admin can view all notifications
        if user_role == "admin":
            return True

        # Users can view notifications for their role or specifically for them
        if obj.recipient == request.user:
            return True

        if obj.recipient_role in [user_role, "all"]:
            # But non-admin users cannot view payment notifications
            if user_role != "admin" and obj.notification_type in [
                "payment",
                "student_payment",
                "teacher_payment",
            ]:
                return False
            return True

        return False

    def validate(self, data):
        """Validate notification data based on role restrictions"""
        notification_type = data.get("notification_type")
        recipient_role = data.get("recipient_role")

        # Payment notifications must be for admin only
        if notification_type in ["payment", "student_payment", "teacher_payment"]:
            if recipient_role != "admin":
                raise serializers.ValidationError(
                    "Payment notifications can only be sent to admin users."
                )

        return data


class PaymentNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentNotification model (admin only).
    """

    notification = NotificationSerializer(read_only=True)
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = PaymentNotification
        fields = [
            "id",
            "notification",
            "payment_type",
            "payment_status",
            "amount",
            "currency",
            "student",
            "student_name",
            "teacher",
            "teacher_name",
            "payment_reference",
            "due_date",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "student_name",
            "teacher_name",
        ]

    def get_student_name(self, obj):
        """Get student full name"""
        return obj.student.full_name if obj.student else None

    def get_teacher_name(self, obj):
        """Get teacher full name"""
        return obj.teacher.full_name if obj.teacher else None

    def validate(self, data):
        """Validate payment notification data"""
        request = self.context.get("request")
        if request and request.user:
            user_role = Notification.get_user_role(request.user)
            if user_role != "admin":
                raise serializers.ValidationError(
                    "Only admin users can create payment notifications."
                )
        return data


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model with role-based fields.
    """

    user_role = serializers.SerializerMethodField()

    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "user",
            "email_notifications",
            "push_notifications",
            "assignment_notifications",
            "submission_notifications",
            "progress_notifications",
            "schedule_notifications",
            "payment_notifications",
            "student_payment_notifications",
            "teacher_payment_notifications",
            "digest_frequency",
            "created_at",
            "updated_at",
            "user_role",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "user_role"]

    def get_user_role(self, obj):
        """Get user role"""
        return Notification.get_user_role(obj.user)

    def validate(self, data):
        """Validate preferences based on user role"""
        instance = getattr(self, "instance", None)
        user = instance.user if instance else self.context.get("request").user

        if user:
            user_role = Notification.get_user_role(user)

            # Only admin users can have payment notification preferences
            if user_role != "admin":
                data["payment_notifications"] = False
                data["student_payment_notifications"] = False
                data["teacher_payment_notifications"] = False

        return data


class CreateNotificationSerializer(serializers.Serializer):
    """
    Serializer for creating notifications via API.
    """

    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    notification_type = serializers.ChoiceField(choices=Notification.NOTIFICATION_TYPES)
    recipient_role = serializers.ChoiceField(
        choices=Notification.RECIPIENT_ROLES, default="all"
    )
    recipient_id = serializers.IntegerField(required=False, allow_null=True)
    priority = serializers.ChoiceField(
        choices=Notification.PRIORITY_LEVELS, default="medium"
    )

    def validate(self, data):
        """Validate notification creation data"""
        notification_type = data.get("notification_type")
        recipient_role = data.get("recipient_role")

        # Payment notifications must be for admin only
        if notification_type in ["payment", "student_payment", "teacher_payment"]:
            if recipient_role != "admin":
                raise serializers.ValidationError(
                    "Payment notifications can only be sent to admin users."
                )

        # Validate recipient if provided
        recipient_id = data.get("recipient_id")
        if recipient_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                recipient = User.objects.get(id=recipient_id)
                data["recipient"] = recipient
            except User.DoesNotExist:
                raise serializers.ValidationError("Recipient user does not exist.")

        return data


class CreatePaymentNotificationSerializer(serializers.Serializer):
    """
    Serializer for creating payment notifications via API (admin only).
    """

    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    payment_type = serializers.ChoiceField(choices=PaymentNotification.PAYMENT_TYPES)
    payment_status = serializers.ChoiceField(choices=PaymentNotification.PAYMENT_STATUS)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3, default="USD")
    student_id = serializers.IntegerField(required=False, allow_null=True)
    teacher_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    payment_reference = serializers.CharField(
        max_length=100, required=False, allow_null=True
    )

    def validate(self, data):
        """Validate payment notification creation data"""
        # Check if user is admin
        request = self.context.get("request")
        if request and request.user:
            user_role = Notification.get_user_role(request.user)
            if user_role != "admin":
                raise serializers.ValidationError(
                    "Only admin users can create payment notifications."
                )

        # Validate student if provided
        student_id = data.get("student_id")
        if student_id:
            from apps.accounts.models import Student

            try:
                student = Student.objects.get(id=student_id)
                data["student"] = student
            except Student.DoesNotExist:
                raise serializers.ValidationError("Student does not exist.")

        # Validate teacher if provided
        teacher_id = data.get("teacher_id")
        if teacher_id:
            from apps.accounts.models import Teacher

            try:
                teacher = Teacher.objects.get(id=teacher_id)
                data["teacher"] = teacher
            except Teacher.DoesNotExist:
                raise serializers.ValidationError("Teacher does not exist.")

        return data


class MarkNotificationsReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """

    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of notification IDs to mark as read. If empty, marks all as read.",
    )

    def validate_notification_ids(self, value):
        """Validate that notification IDs exist and belong to current user"""
        if value:
            request = self.context.get("request")
            if request and request.user:
                from .utils import get_user_notifications

                user_notifications = get_user_notifications(request.user)
                valid_ids = set(user_notifications.values_list("id", flat=True))
                invalid_ids = set(value) - valid_ids

                if invalid_ids:
                    raise serializers.ValidationError(
                        f"Invalid notification IDs: {list(invalid_ids)}"
                    )

        return value


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics.
    """

    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    read = serializers.IntegerField()
    by_type = serializers.ListField()
    by_priority = serializers.ListField()
