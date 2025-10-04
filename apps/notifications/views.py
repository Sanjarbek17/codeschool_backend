from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Notification, NotificationPreference, PaymentNotification
from .serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
    PaymentNotificationSerializer,
    CreateNotificationSerializer,
    CreatePaymentNotificationSerializer,
    MarkNotificationsReadSerializer,
    NotificationStatsSerializer,
)
from .utils import (
    get_user_notifications,
    bulk_mark_as_read,
    get_notification_stats,
    create_notification,
    create_payment_notification,
    get_or_create_user_preferences,
)


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access certain views.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and Notification.get_user_role(request.user) == "admin"
        )


class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow teachers and admin users.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = Notification.get_user_role(request.user)
        return user_role in ["teacher", "admin"]


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications with role-based filtering.
    Only shows notifications relevant to the user's role.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsTeacherOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["notification_type", "is_read", "priority"]

    def get_queryset(self):
        """
        Return notifications based on user role.
        Teachers and admins only get their relevant notifications.
        """
        return get_user_notifications(self.request.user)

    def get_serializer_context(self):
        """Add request to serializer context"""
        return {"request": self.request}

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read"""
        notification = get_object_or_404(self.get_queryset(), pk=pk)
        notification.mark_as_read()

        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user"""
        serializer = MarkNotificationsReadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get("notification_ids")
        count = bulk_mark_as_read(request.user, notification_ids)

        return Response(
            {"message": f"Marked {count} notifications as read", "count": count}
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get notification statistics for the current user"""
        stats = get_notification_stats(request.user)
        serializer = NotificationStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def unread(self, request):
        """Get only unread notifications"""
        unread_notifications = get_user_notifications(request.user, unread_only=True)
        page = self.paginate_queryset(unread_notifications)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def create_notification(self, request):
        """Create a new notification (admin only)"""
        serializer = CreateNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        recipient = validated_data.pop("recipient", None)

        notification = create_notification(recipient=recipient, **validated_data)

        response_serializer = NotificationSerializer(
            notification, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PaymentNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payment notifications (admin only).
    """

    serializer_class = PaymentNotificationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["payment_type", "payment_status", "student", "teacher"]

    def get_queryset(self):
        """Return all payment notifications for admin users"""
        return PaymentNotification.objects.all()

    def get_serializer_context(self):
        """Add request to serializer context"""
        return {"request": self.request}

    @action(detail=False, methods=["post"])
    def create_payment_notification(self, request):
        """Create a new payment notification"""
        serializer = CreatePaymentNotificationSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        student = validated_data.pop("student", None)
        teacher = validated_data.pop("teacher", None)

        payment_notification = create_payment_notification(
            student=student, teacher=teacher, **validated_data
        )

        response_serializer = PaymentNotificationSerializer(
            payment_notification, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notification preferences.
    Users can only view and edit their own preferences.
    """

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's preferences"""
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create user's notification preferences"""
        return get_or_create_user_preferences(self.request.user)

    def get_serializer_context(self):
        """Add request to serializer context"""
        return {"request": self.request}

    @action(detail=False, methods=["get"])
    def my_preferences(self, request):
        """Get current user's notification preferences"""
        preferences = get_or_create_user_preferences(request.user)
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)

    @action(detail=False, methods=["put", "patch"])
    def update_preferences(self, request):
        """Update current user's notification preferences"""
        preferences = get_or_create_user_preferences(request.user)
        serializer = self.get_serializer(
            preferences, data=request.data, partial=request.method == "PATCH"
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
