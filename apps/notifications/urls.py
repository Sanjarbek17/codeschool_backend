from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    PaymentNotificationViewSet,
    NotificationPreferenceViewSet,
)

app_name = "notifications"

# Create router and register viewsets
router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(
    r"payment-notifications",
    PaymentNotificationViewSet,
    basename="payment-notification",
)
router.register(
    r"preferences", NotificationPreferenceViewSet, basename="notification-preference"
)

urlpatterns = [
    path("api/", include(router.urls)),
]
