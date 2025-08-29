from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Used as the base authentication model for the system.
    """

    class Meta:
        db_table = "auth_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Teacher(models.Model):
    """
    Teacher profile model extending the base User model.
    Contains teacher-specific information and relationships.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="teacher_profile"
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)

    # Additional teacher-specific fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_teacher"
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Group(models.Model):
    """
    Group model representing a class or group that can be taught by multiple teachers
    and attended by multiple students.
    """

    name = models.CharField(max_length=200, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)
    teachers = models.ManyToManyField(
        Teacher,
        related_name="groups",
        blank=True,
        help_text="Teachers who can teach this group",
    )

    # Additional group-specific fields
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_group"
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def teacher_count(self):
        """Returns the number of teachers assigned to this group"""
        return self.teachers.count()

    @property
    def student_count(self):
        """Returns the number of students in this group"""
        return self.students.count()


class Student(models.Model):
    """
    Student profile model extending the base User model.
    Contains student-specific information including parent contact details.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    parents_phone_number = models.CharField(max_length=20)
    groups = models.ManyToManyField(
        Group,
        related_name="students",
        blank=True,
        help_text="Groups this student attends",
    )

    # Additional student-specific fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_student"
        verbose_name = "Student"
        verbose_name_plural = "Students"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
