"""
Tests for payment-based access control to educational content.
Verifies that students with different payment statuses have appropriate access levels.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta

from apps.accounts.models import Student, Teacher, Group
from apps.courses.models import Course, Lessons
from apps.assignments.models import Homework, Task
from apps.admin_panel.models import Payment, StudentPaymentStatus

User = get_user_model()


class PaymentBasedAccessControlTest(TestCase):
    """Test payment-based access control for educational content"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123", is_staff=True
        )

        self.teacher_user = User.objects.create_user(
            username="teacher", password="testpass123"
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name="John",
            last_name="Teacher",
            phone_number="+1234567890",
        )

        # Create student users with different payment statuses
        self.active_student_user = User.objects.create_user(
            username="active_student", password="testpass123"
        )
        self.active_student = Student.objects.create(
            user=self.active_student_user,
            first_name="Active",
            last_name="Student",
            phone_number="+1234567890",
            parents_phone_number="+1234567800",
        )

        self.warning_student_user = User.objects.create_user(
            username="warning_student", password="testpass123"
        )
        self.warning_student = Student.objects.create(
            user=self.warning_student_user,
            first_name="Warning",
            last_name="Student",
            phone_number="+1234567891",
            parents_phone_number="+1234567801",
        )

        self.suspended_student_user = User.objects.create_user(
            username="suspended_student", password="testpass123"
        )
        self.suspended_student = Student.objects.create(
            user=self.suspended_student_user,
            first_name="Suspended",
            last_name="Student",
            phone_number="+1234567892",
            parents_phone_number="+1234567802",
        )

        self.expelled_student_user = User.objects.create_user(
            username="expelled_student", password="testpass123"
        )
        self.expelled_student = Student.objects.create(
            user=self.expelled_student_user,
            first_name="Expelled",
            last_name="Student",
            phone_number="+1234567893",
            parents_phone_number="+1234567803",
        )

        # Create group and course
        self.group = Group.objects.create(name="Test Group")
        self.course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            duration_weeks=10,
            level="beginner",
        )

        # Create lesson and homework
        self.lesson = Lessons.objects.create(
            title="Test Lesson",
            description="Test Description",
            content="Test Content",
            course=self.course,
            order=1,
        )

        self.homework = Homework.objects.create(
            lesson=self.lesson,
            title="Test Homework",
            description="Test homework description",
        )

        self.task = Task.objects.create(
            homework=self.homework,
            title="Test Task",
            description="Test task description",
        )

        # Create payment statuses
        StudentPaymentStatus.objects.create(
            student=self.active_student_user, status="active"
        )

        StudentPaymentStatus.objects.create(
            student=self.warning_student_user,
            status="warning",
            consecutive_unpaid_months=1,
        )

        StudentPaymentStatus.objects.create(
            student=self.suspended_student_user,
            status="suspended",
            consecutive_unpaid_months=2,
        )

        StudentPaymentStatus.objects.create(
            student=self.expelled_student_user,
            status="expelled",
            consecutive_unpaid_months=4,
        )

    def test_admin_access_all_content(self):
        """Test that admin users can access all content regardless of payment status"""
        self.client.force_authenticate(user=self.admin_user)

        # Test lesson access
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test homework access
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test task access
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_teacher_access_all_content(self):
        """Test that teachers can access all content regardless of payment status"""
        self.client.force_authenticate(user=self.teacher_user)

        # Test lesson access
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test homework access
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test task access
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_active_student_access(self):
        """Test that active students can access all content"""
        self.client.force_authenticate(user=self.active_student_user)

        # Test lesson access
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test homework access
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test task access
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_warning_student_limited_access(self):
        """Test that warning students have limited access to lessons but no homework access"""
        self.client.force_authenticate(user=self.warning_student_user)

        # Warning students can view lessons (read-only)
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # But cannot access homework
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("overdue payment", response.data["detail"].lower())

        # Cannot access tasks
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_suspended_student_no_access(self):
        """Test that suspended students cannot access any educational content"""
        self.client.force_authenticate(user=self.suspended_student_user)

        # Cannot access lessons
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("suspended", response.data["detail"].lower())

        # Cannot access homework
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("suspended", response.data["detail"].lower())

        # Cannot access tasks
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_expelled_student_no_access(self):
        """Test that expelled students cannot access any educational content"""
        self.client.force_authenticate(user=self.expelled_student_user)

        # Cannot access lessons
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("expelled", response.data["detail"].lower())

        # Cannot access homework
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("expelled", response.data["detail"].lower())

        # Cannot access tasks
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_no_access(self):
        """Test that unauthenticated users cannot access any content"""
        # Don't authenticate

        # Cannot access lessons
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Cannot access homework
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Cannot access tasks
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_student_default_access(self):
        """Test that new students without payment status have default access"""
        # Create a new student without payment status
        new_user = User.objects.create_user(
            username="newstudent", password="testpass123"
        )
        new_student = Student.objects.create(
            user=new_user,
            first_name="New",
            last_name="Student",
            phone_number="+1234567894",
            parents_phone_number="+1234567804",
        )

        self.client.force_authenticate(user=new_user)

        # Should have access to all content (default to active)
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payment_status_change_affects_access(self):
        """Test that changing payment status immediately affects access"""
        self.client.force_authenticate(user=self.active_student_user)

        # Initially can access content
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Change status to suspended
        payment_status = StudentPaymentStatus.objects.get(
            student=self.active_student_user
        )
        payment_status.status = "suspended"
        payment_status.save()

        # Now should be denied access
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Change back to active
        payment_status.status = "active"
        payment_status.save()

        # Should regain access
        response = self.client.get("/api/homework/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PaymentStatusUtilityTest(TestCase):
    """Test utility functions for payment status checking"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.student = Student.objects.create(
            user=self.user,
            first_name="Test",
            last_name="Student",
            phone_number="+1234567890",
            parents_phone_number="+1234567800",
        )

    def test_get_student_payment_status(self):
        """Test get_student_payment_status utility function"""
        from apps.admin_panel.permissions import get_student_payment_status

        # No status exists - should return 'active'
        status = get_student_payment_status(self.user)
        self.assertEqual(status, "active")

        # Create status
        StudentPaymentStatus.objects.create(student=self.user, status="warning")

        # Should return actual status
        status = get_student_payment_status(self.user)
        self.assertEqual(status, "warning")

    def test_is_student_suspended(self):
        """Test is_student_suspended utility function"""
        from apps.admin_panel.permissions import is_student_suspended

        # No status - should return False
        self.assertFalse(is_student_suspended(self.user))

        # Active status - should return False
        StudentPaymentStatus.objects.create(student=self.user, status="active")
        self.assertFalse(is_student_suspended(self.user))

        # Suspended status - should return True
        payment_status = StudentPaymentStatus.objects.get(student=self.user)
        payment_status.status = "suspended"
        payment_status.save()
        self.assertTrue(is_student_suspended(self.user))

    def test_can_student_access_content(self):
        """Test can_student_access_content utility function"""
        from apps.admin_panel.permissions import can_student_access_content

        # No status - should return True (default active)
        self.assertTrue(can_student_access_content(self.user))

        # Warning status - should return True (grace period)
        StudentPaymentStatus.objects.create(student=self.user, status="warning")
        self.assertTrue(can_student_access_content(self.user))

        # Suspended status - should return False
        payment_status = StudentPaymentStatus.objects.get(student=self.user)
        payment_status.status = "suspended"
        payment_status.save()
        self.assertFalse(can_student_access_content(self.user))

    def test_can_student_submit_assignments(self):
        """Test can_student_submit_assignments utility function"""
        from apps.admin_panel.permissions import can_student_submit_assignments

        # Active status - should return True
        StudentPaymentStatus.objects.create(student=self.user, status="active")
        self.assertTrue(can_student_submit_assignments(self.user))

        # Warning status - should return False (no assignment submission)
        payment_status = StudentPaymentStatus.objects.get(student=self.user)
        payment_status.status = "warning"
        payment_status.save()
        self.assertFalse(can_student_submit_assignments(self.user))
