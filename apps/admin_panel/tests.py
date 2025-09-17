from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import Payment
from apps.accounts.models import Student, Group, Teacher
from apps.courses.models import Course

User = get_user_model()


class PaymentModelTest(TestCase):
    """Test Payment model functionality"""

    def setUp(self):
        # Create test users
        self.student_user = User.objects.create_user(
            username="student1",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )

        self.teacher_user = User.objects.create_user(
            username="teacher1",
            password="testpass123",
            first_name="Jane",
            last_name="Smith",
        )

        self.admin_user = User.objects.create_user(
            username="admin1", password="testpass123", is_staff=True, is_superuser=True
        )

        # Create test student
        self.student = Student.objects.create(
            user=self.student_user,
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            parents_phone_number="0987654321",
        )

        # Create test teacher
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name="Jane",
            last_name="Smith",
            phone_number="1111111111",
        )

        # Create test course
        self.course = Course.objects.create(
            title="Python Basics",
            description="Learn Python programming",
            duration_weeks=12,
            level="beginner",
        )

        # Create test group
        self.group = Group.objects.create(
            name="Python Group 1", current_course=self.course
        )
        self.group.teachers.add(self.teacher)
        self.student.groups.add(self.group)

    def test_payment_creation(self):
        """Test creating a payment"""
        payment = Payment.objects.create(
            student=self.student_user,
            group=self.group,
            course=self.course,
            amount=Decimal("100.00"),
            due_date=date.today() + timedelta(days=30),
            month=1,
            year=2025,
        )

        self.assertEqual(payment.student, self.student_user)
        self.assertEqual(payment.group, self.group)
        self.assertEqual(payment.course, self.course)
        self.assertEqual(payment.amount, Decimal("100.00"))
        self.assertEqual(payment.status, "pending")
        self.assertFalse(payment.is_overdue)

    def test_payment_overdue(self):
        """Test payment overdue functionality"""
        past_date = date.today() - timedelta(days=5)
        payment = Payment.objects.create(
            student=self.student_user,
            group=self.group,
            course=self.course,
            amount=Decimal("100.00"),
            due_date=past_date,
            month=1,
            year=2025,
        )

        self.assertTrue(payment.is_overdue)
        self.assertEqual(payment.days_overdue, 5)

    def test_mark_as_paid(self):
        """Test marking payment as paid"""
        payment = Payment.objects.create(
            student=self.student_user,
            group=self.group,
            course=self.course,
            amount=Decimal("100.00"),
            due_date=date.today() + timedelta(days=30),
            month=1,
            year=2025,
        )

        payment.mark_as_paid(
            payment_method="cash", processed_by=self.admin_user, notes="Paid in full"
        )

        self.assertEqual(payment.status, "paid")
        self.assertEqual(payment.payment_method, "cash")
        self.assertEqual(payment.processed_by, self.admin_user)
        self.assertEqual(payment.notes, "Paid in full")
        self.assertIsNotNone(payment.paid_date)

    def test_create_monthly_payments(self):
        """Test creating monthly payments for all students"""
        # Create more test data
        student_user2 = User.objects.create_user(
            username="student2", password="testpass123"
        )
        student2 = Student.objects.create(
            user=student_user2,
            first_name="Alice",
            last_name="Johnson",
            phone_number="2222222222",
            parents_phone_number="3333333333",
        )
        student2.groups.add(self.group)

        # Create payments for current month
        created_payments = Payment.create_monthly_payments(1, 2025, Decimal("150.00"))

        # Should create 2 payments (one for each student)
        self.assertEqual(len(created_payments), 2)

        # Verify payment details
        payment1 = Payment.objects.get(student=self.student_user)
        self.assertEqual(payment1.amount, Decimal("150.00"))
        self.assertEqual(payment1.month, 1)
        self.assertEqual(payment1.year, 2025)

        payment2 = Payment.objects.get(student=student_user2)
        self.assertEqual(payment2.amount, Decimal("150.00"))
        self.assertEqual(payment2.month, 1)
        self.assertEqual(payment2.year, 2025)

    def test_update_overdue_payments(self):
        """Test updating overdue payments"""
        # Create a payment that's past due
        past_date = date.today() - timedelta(days=3)
        payment = Payment.objects.create(
            student=self.student_user,
            group=self.group,
            course=self.course,
            amount=Decimal("100.00"),
            due_date=past_date,
            month=1,
            year=2025,
            status="pending",
        )

        # Update overdue payments
        updated_count = Payment.update_overdue_payments()

        self.assertEqual(updated_count, 1)

        # Refresh from database
        payment.refresh_from_db()
        self.assertEqual(payment.status, "overdue")

    def test_payment_summary(self):
        """Test student payment summary"""
        # Create multiple payments
        Payment.objects.create(
            student=self.student_user,
            group=self.group,
            course=self.course,
            amount=Decimal("100.00"),
            paid_amount=Decimal("100.00"),  # Set paid_amount for paid status
            due_date=date.today() + timedelta(days=30),
            month=1,
            year=2025,
            status="paid",
        )

        Payment.objects.create(
            student=self.student_user,
            group=self.group,
            course=self.course,
            amount=Decimal("100.00"),
            due_date=date.today() + timedelta(days=30),
            month=2,
            year=2025,
            status="pending",
        )

        # Get summary
        summary = Payment.get_student_payment_summary(self.student_user)

        self.assertEqual(summary["total_payments"], 2)
        self.assertEqual(summary["paid_count"], 1)
        self.assertEqual(summary["pending_count"], 1)
        self.assertEqual(summary["total_amount_due"], Decimal("200.00"))
        self.assertEqual(summary["total_paid_amount"], Decimal("100.00"))
        self.assertEqual(summary["outstanding_amount"], Decimal("100.00"))


class PaymentViewsTest(TestCase):
    """Test Payment views and API endpoints"""

    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123", is_staff=True, is_superuser=True
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            username="regular", password="testpass123"
        )

    def test_admin_dashboard_requires_admin(self):
        """Test that admin dashboard requires admin permissions"""
        from django.test import Client
        from django.urls import reverse
        from rest_framework.authtoken.models import Token

        client = Client()

        # Try without authentication
        response = client.get("/api/admin-panel/dashboard/")
        self.assertEqual(response.status_code, 401)

        # Try with regular user
        token = Token.objects.create(user=self.regular_user)
        client.defaults["HTTP_AUTHORIZATION"] = f"Token {token.key}"
        response = client.get("/api/admin-panel/dashboard/")
        self.assertEqual(response.status_code, 403)

        # Try with admin user
        admin_token = Token.objects.create(user=self.admin_user)
        client.defaults["HTTP_AUTHORIZATION"] = f"Token {admin_token.key}"
        response = client.get("/api/admin-panel/dashboard/")
        self.assertEqual(response.status_code, 200)
