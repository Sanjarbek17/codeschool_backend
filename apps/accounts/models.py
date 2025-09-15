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

    # Current course being taught in this group
    current_course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_groups",
        help_text="The course currently being taught in this group",
    )

    # Current lesson being taught in this group
    current_lesson = models.ForeignKey(
        "courses.Lessons",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_groups",
        help_text="The lesson currently being taught in this group",
    )

    # Track when the current lesson was last taught
    last_taught_date = models.DateTimeField(
        null=True, blank=True, help_text="When the current lesson was last taught"
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

    @property
    def current_lesson_info(self):
        """Returns current lesson information if available"""
        if self.current_lesson:
            return {
                "id": self.current_lesson.id,
                "title": self.current_lesson.title,
                "description": self.current_lesson.description,
                "order": self.current_lesson.order,
                "course_title": self.current_lesson.course.title,
                "last_taught": self.last_taught_date,
            }
        return None

    @property
    def current_course_info(self):
        """Returns current course information if available"""
        if self.current_course:
            return {
                "id": self.current_course.id,
                "title": self.current_course.title,
                "level": self.current_course.level,
                "duration_weeks": self.current_course.duration_weeks,
            }
        return None

    def set_current_lesson(self, lesson, taught_date=None):
        """Set the current lesson and update the last taught date"""
        from django.utils import timezone

        self.current_lesson = lesson
        if lesson:
            self.current_course = lesson.course
        self.last_taught_date = taught_date or timezone.now()
        self.save()

    def set_current_course(self, course):
        """Set the current course"""
        self.current_course = course
        # Reset current lesson when changing course
        self.current_lesson = None
        self.last_taught_date = None
        self.save()

    def get_all_lessons(self):
        """Get all lessons that have been taught in this group"""
        from apps.courses.models import Lessons

        return Lessons.objects.filter(attendances__group=self).distinct()


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
