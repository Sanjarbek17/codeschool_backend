from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import Notification, NotificationPreference, PaymentNotification
from .utils import (
    create_notification,
    create_payment_notification,
    get_user_notifications,
)
from apps.accounts.models import Teacher, Student, Group
from apps.assignments.models import Homework
from apps.courses.models import Course, Lessons

User = get_user_model()


class NotificationModelTest(TestCase):
    """Test cases for Notification model"""

    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher", email="teacher@test.com", password="testpass123"
        )

        self.student_user = User.objects.create_user(
            username="student", email="student@test.com", password="testpass123"
        )

        # Create profiles
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
        )

        self.student = Student.objects.create(
            user=self.student_user,
            first_name="Jane",
            last_name="Smith",
            phone_number="0987654321",
            parents_phone_number="1122334455",
        )

    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            title="Test Notification",
            message="This is a test notification",
            notification_type="assignment",
            recipient_role="teacher",
            recipient=self.teacher_user,
        )

        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.recipient_role, "teacher")
        self.assertFalse(notification.is_read)

    def test_get_user_role(self):
        """Test user role detection"""
        admin_role = Notification.get_user_role(self.admin_user)
        teacher_role = Notification.get_user_role(self.teacher_user)
        student_role = Notification.get_user_role(self.student_user)

        self.assertEqual(admin_role, "admin")
        self.assertEqual(teacher_role, "teacher")
        self.assertEqual(student_role, "student")

    def test_payment_notification_validation(self):
        """Test that payment notifications can only be for admin"""
        # This should work
        notification = Notification.objects.create(
            title="Payment Notification",
            message="Payment received",
            notification_type="payment",
            recipient_role="admin",
        )
        notification.full_clean()  # Should not raise

        # This should fail validation
        notification_invalid = Notification(
            title="Payment Notification",
            message="Payment received",
            notification_type="payment",
            recipient_role="teacher",
        )

        with self.assertRaises(Exception):
            notification_invalid.full_clean()

    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            title="Test Notification",
            message="This is a test notification",
            notification_type="assignment",
            recipient_role="teacher",
            recipient=self.teacher_user,
        )

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

        notification.mark_as_read()

        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)


class NotificationUtilsTest(TestCase):
    """Test cases for notification utility functions"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher", email="teacher@test.com", password="testpass123"
        )

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
        )

    def test_create_notification_util(self):
        """Test create_notification utility function"""
        notification = create_notification(
            title="Test Notification",
            message="Test message",
            notification_type="assignment",
            recipient_role="teacher",
            recipient=self.teacher_user,
        )

        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.recipient, self.teacher_user)

    def test_create_payment_notification_util(self):
        """Test create_payment_notification utility function"""
        payment_notification = create_payment_notification(
            title="Payment Received",
            message="Student payment received",
            payment_type="tuition",
            payment_status="completed",
            amount=500.00,
            currency="USD",
        )

        self.assertIsInstance(payment_notification, PaymentNotification)
        self.assertEqual(payment_notification.amount, 500.00)
        self.assertEqual(payment_notification.payment_type, "tuition")
        self.assertEqual(payment_notification.notification.recipient_role, "admin")

    def test_get_user_notifications(self):
        """Test getting user notifications based on role"""
        # Create notifications for different roles
        admin_notification = create_notification(
            title="Admin Notification",
            message="For admin only",
            notification_type="announcement",
            recipient_role="admin",
        )

        teacher_notification = create_notification(
            title="Teacher Notification",
            message="For teachers only",
            notification_type="assignment",
            recipient_role="teacher",
        )

        all_notification = create_notification(
            title="All Users Notification",
            message="For all users",
            notification_type="announcement",
            recipient_role="all",
        )

        # Test admin user sees admin and all notifications
        admin_notifications = get_user_notifications(self.admin_user)
        self.assertIn(admin_notification, admin_notifications)
        self.assertIn(all_notification, admin_notifications)
        # Admin should see all notifications since they have admin role

        # Test teacher user sees teacher and all notifications
        teacher_notifications = get_user_notifications(self.teacher_user)
        self.assertIn(teacher_notification, teacher_notifications)
        self.assertIn(all_notification, teacher_notifications)
        self.assertNotIn(admin_notification, teacher_notifications)


class NotificationAPITest(APITestCase):
    """Test cases for Notification API endpoints"""

    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher", email="teacher@test.com", password="testpass123"
        )

        self.student_user = User.objects.create_user(
            username="student", email="student@test.com", password="testpass123"
        )

        # Create profiles
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
        )

        self.student = Student.objects.create(
            user=self.student_user,
            first_name="Jane",
            last_name="Smith",
            phone_number="0987654321",
            parents_phone_number="1122334455",
        )

        # Create tokens
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.teacher_token = Token.objects.create(user=self.teacher_user)
        self.student_token = Token.objects.create(user=self.student_user)

        # Create test notifications
        self.teacher_notification = create_notification(
            title="Teacher Notification",
            message="For teachers",
            notification_type="assignment",
            recipient_role="teacher",
        )

        self.admin_notification = create_notification(
            title="Admin Notification",
            message="For admin",
            notification_type="announcement",
            recipient_role="admin",
        )

    def test_teacher_can_access_notifications(self):
        """Test that teachers can access their notifications"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.teacher_token.key}")

        url = reverse("notifications:notification-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or direct list
        if "results" in response.data:
            self.assertGreaterEqual(len(response.data["results"]), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)

    def test_student_cannot_access_notifications(self):
        """Test that students cannot access notifications API"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.student_token.key}")

        url = reverse("notifications:notification-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_all_notifications(self):
        """Test that admin can access all notifications"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        url = reverse("notifications:notification-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or direct list
        if "results" in response.data:
            self.assertGreaterEqual(len(response.data["results"]), 2)
        else:
            self.assertGreaterEqual(len(response.data), 2)

    def test_mark_notification_as_read(self):
        """Test marking a notification as read"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.teacher_token.key}")

        url = reverse(
            "notifications:notification-mark-read",
            kwargs={"pk": self.teacher_notification.id},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh notification from database
        self.teacher_notification.refresh_from_db()
        self.assertTrue(self.teacher_notification.is_read)

    def test_get_notification_stats(self):
        """Test getting notification statistics"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.teacher_token.key}")

        url = reverse("notifications:notification-stats")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total", response.data)
        self.assertIn("unread", response.data)
        self.assertIn("read", response.data)

    def test_admin_can_create_payment_notification(self):
        """Test that admin can create payment notifications"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        url = reverse("notifications:payment-notification-create-payment-notification")
        data = {
            "title": "Payment Received",
            "message": "Student payment received",
            "payment_type": "tuition",
            "payment_status": "completed",
            "amount": "500.00",
            "currency": "USD",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentNotification.objects.count(), 1)

    def test_teacher_cannot_create_payment_notification(self):
        """Test that teachers cannot create payment notifications"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.teacher_token.key}")

        url = reverse("notifications:payment-notification-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class NotificationPreferenceTest(TestCase):
    """Test cases for notification preferences"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher", email="teacher@test.com", password="testpass123"
        )

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
        )

    def test_admin_payment_preferences(self):
        """Test that admin users can have payment notification preferences"""
        preferences = NotificationPreference.objects.create(
            user=self.admin_user,
            payment_notifications=True,
            student_payment_notifications=True,
            teacher_payment_notifications=True,
        )

        preferences.full_clean()  # Should not raise
        self.assertTrue(preferences.payment_notifications)

    def test_teacher_payment_preferences_disabled(self):
        """Test that teacher payment preferences are automatically disabled"""
        preferences = NotificationPreference.objects.create(
            user=self.teacher_user,
            payment_notifications=True,  # This should be overridden
            student_payment_notifications=True,  # This should be overridden
            teacher_payment_notifications=True,  # This should be overridden
        )

        preferences.clean()  # This should disable payment preferences

        self.assertFalse(preferences.payment_notifications)
        self.assertFalse(preferences.student_payment_notifications)
        self.assertFalse(preferences.teacher_payment_notifications)
