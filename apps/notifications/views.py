from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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

    @swagger_auto_schema(
        operation_description="List notifications based on user role",
        operation_summary="List Notifications",
        tags=["Notifications"],
        responses={200: NotificationSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new notification",
        operation_summary="Create Notification",
        tags=["Notifications"],
        request_body=NotificationSerializer,
        responses={201: NotificationSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve detailed notification information",
        operation_summary="Get Notification Detail",
        tags=["Notifications"],
        responses={200: NotificationSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a notification",
        operation_summary="Update Notification",
        tags=["Notifications"],
        request_body=NotificationSerializer,
        responses={200: NotificationSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a notification",
        operation_summary="Partially Update Notification",
        tags=["Notifications"],
        request_body=NotificationSerializer,
        responses={200: NotificationSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a notification",
        operation_summary="Delete Notification",
        tags=["Notifications"],
        responses={204: "Notification deleted successfully"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return notifications based on user role.
        Teachers and admins only get their relevant notifications.
        """
        return get_user_notifications(self.request.user)

    def get_serializer_context(self):
        """Add request to serializer context"""
        return {"request": self.request}

    @swagger_auto_schema(
        operation_description="Mark a specific notification as read",
        operation_summary="Mark Notification as Read",
        tags=["Notifications"],
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT),
        responses={200: NotificationSerializer},
    )
    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read"""
        notification = get_object_or_404(self.get_queryset(), pk=pk)
        notification.mark_as_read()

        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Mark all notifications as read for the current user",
        operation_summary="Mark All Notifications as Read",
        tags=["Notifications"],
        request_body=MarkNotificationsReadSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "count": openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            )
        },
    )
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

    @swagger_auto_schema(
        operation_description="Get notification statistics for the current user",
        operation_summary="Get Notification Statistics",
        tags=["Notifications"],
        responses={200: NotificationStatsSerializer},
    )
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get notification statistics for the current user"""
        stats = get_notification_stats(request.user)
        serializer = NotificationStatsSerializer(stats)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get only unread notifications",
        operation_summary="Get Unread Notifications",
        tags=["Notifications"],
        responses={200: NotificationSerializer(many=True)},
    )
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

    @swagger_auto_schema(
        operation_description="Create a new notification (admin only)",
        operation_summary="Create Notification (Admin)",
        tags=["Notifications"],
        request_body=CreateNotificationSerializer,
        responses={201: NotificationSerializer},
    )
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

    @swagger_auto_schema(
        operation_description="Manually trigger bulk payment check (admin only)",
        operation_summary="Trigger Payment Check",
        tags=["Notifications"],
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "notifications_sent": openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            )
        },
    )
    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def trigger_payment_check(self, request):
        """Manually trigger bulk payment check (admin only)"""
        from .signals import trigger_bulk_payment_check

        try:
            notifications_sent = trigger_bulk_payment_check()
            return Response(
                {
                    "success": True,
                    "message": f"Payment check completed. Sent {notifications_sent} notifications.",
                    "notifications_sent": notifications_sent,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": f"Error during payment check: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaymentNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payment-specific notifications.
    Includes additional payment-related functionality.
    """

    serializer_class = PaymentNotificationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["payment_type", "payment_status", "student", "teacher"]

    @swagger_auto_schema(
        operation_description="List payment notifications",
        operation_summary="List Payment Notifications",
        tags=["Notifications"],
        responses={200: PaymentNotificationSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new payment notification",
        operation_summary="Create Payment Notification",
        tags=["Notifications"],
        request_body=PaymentNotificationSerializer,
        responses={201: PaymentNotificationSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve detailed payment notification information",
        operation_summary="Get Payment Notification Detail",
        tags=["Notifications"],
        responses={200: PaymentNotificationSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a payment notification",
        operation_summary="Update Payment Notification",
        tags=["Notifications"],
        request_body=PaymentNotificationSerializer,
        responses={200: PaymentNotificationSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a payment notification",
        operation_summary="Partially Update Payment Notification",
        tags=["Notifications"],
        request_body=PaymentNotificationSerializer,
        responses={200: PaymentNotificationSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a payment notification",
        operation_summary="Delete Payment Notification",
        tags=["Notifications"],
        responses={204: "Payment notification deleted successfully"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Return all payment notifications for admin users"""
        return PaymentNotification.objects.all()

    def get_serializer_context(self):
        """Add request to serializer context"""
        return {"request": self.request}

    @swagger_auto_schema(
        operation_description="Create a new payment notification",
        operation_summary="Create Payment Notification (Advanced)",
        tags=["Notifications"],
        request_body=CreatePaymentNotificationSerializer,
        responses={201: PaymentNotificationSerializer},
    )
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

    @swagger_auto_schema(
        operation_description="List notification preferences for the current user",
        operation_summary="List Notification Preferences",
        tags=["Notifications"],
        responses={200: NotificationPreferenceSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create notification preferences",
        operation_summary="Create Notification Preferences",
        tags=["Notifications"],
        request_body=NotificationPreferenceSerializer,
        responses={201: NotificationPreferenceSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve notification preferences",
        operation_summary="Get Notification Preferences Detail",
        tags=["Notifications"],
        responses={200: NotificationPreferenceSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update notification preferences",
        operation_summary="Update Notification Preferences",
        tags=["Notifications"],
        request_body=NotificationPreferenceSerializer,
        responses={200: NotificationPreferenceSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update notification preferences",
        operation_summary="Partially Update Notification Preferences",
        tags=["Notifications"],
        request_body=NotificationPreferenceSerializer,
        responses={200: NotificationPreferenceSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete notification preferences",
        operation_summary="Delete Notification Preferences",
        tags=["Notifications"],
        responses={204: "Notification preferences deleted successfully"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Return only the current user's preferences"""
        # Handle schema generation case where user might be AnonymousUser
        if getattr(self, "swagger_fake_view", False):
            return NotificationPreference.objects.none()
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create user's notification preferences"""
        # Handle schema generation case where user might be AnonymousUser
        if getattr(self, "swagger_fake_view", False):
            return NotificationPreference()
        return get_or_create_user_preferences(self.request.user)

    def get_serializer_context(self):
        """Add request to serializer context"""
        return {"request": self.request}

    @swagger_auto_schema(
        operation_description="Get current user's notification preferences",
        operation_summary="Get My Notification Preferences",
        tags=["Notifications"],
        responses={200: NotificationPreferenceSerializer},
    )
    @action(detail=False, methods=["get"])
    def my_preferences(self, request):
        """Get current user's notification preferences"""
        preferences = get_or_create_user_preferences(request.user)
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)

    @swagger_auto_schema(
        methods=["put"],
        operation_description="Update current user's notification preferences (full update)",
        operation_summary="Update My Notification Preferences (PUT)",
        tags=["Notifications"],
        request_body=NotificationPreferenceSerializer,
        responses={200: NotificationPreferenceSerializer},
    )
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
