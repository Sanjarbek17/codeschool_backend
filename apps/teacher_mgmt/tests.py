from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from apps.accounts.models import Teacher, Student, Group

User = get_user_model()


class TeacherManagementTestCase(APITestCase):
    def setUp(self):
        # Create test user and teacher
        self.user = User.objects.create_user(
            username="teacher1", email="teacher@example.com", password="testpass123"
        )
        self.teacher = Teacher.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            phone_number="+1234567890",
        )

        # Create test group
        self.group = Group.objects.create(name="Test Group")
        self.group.teachers.add(self.teacher)

        # Create test students
        for i in range(3):
            student_user = User.objects.create_user(
                username=f"student{i+1}",
                email=f"student{i+1}@example.com",
                password="testpass123",
            )
            student = Student.objects.create(
                user=student_user,
                first_name=f"Student{i+1}",
                last_name="Test",
                phone_number=f"+123456789{i}",
                parents_phone_number=f"+987654321{i}",
            )
            student.groups.add(self.group)

        # Get token for authentication
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_teacher_dashboard(self):
        """Test teacher dashboard endpoint"""
        response = self.client.get("/api/teachers/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["teacher_info"]["first_name"], "John")
        self.assertEqual(data["total_groups"], 1)
        self.assertEqual(data["total_students"], 3)

    def test_teacher_groups(self):
        """Test teacher groups endpoint"""
        response = self.client.get("/api/teachers/groups/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Test Group")

    def test_teacher_students(self):
        """Test teacher students endpoint"""
        response = self.client.get("/api/teachers/students/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 3)

    def test_teacher_group_detail(self):
        """Test teacher group detail endpoint"""
        response = self.client.get(f"/api/teachers/groups/{self.group.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["name"], "Test Group")
        self.assertEqual(len(data["students"]), 3)

    def test_unauthorized_access(self):
        """Test that non-teachers cannot access teacher endpoints"""
        # Create a regular user without teacher profile
        regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="testpass123"
        )
        token = Token.objects.create(user=regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get("/api/teachers/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
