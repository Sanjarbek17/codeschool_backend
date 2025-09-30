from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta


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

    def get_week_schedule(self, week_start=None):
        """
        Returns the teacher's schedule for a given week, showing 3 lessons per week.
        week_start: datetime.date for the Monday of the week (defaults to current week).
        """
        from django.utils import timezone
        from datetime import timedelta

        if not week_start:
            today = timezone.now().date()
            week_start = today - timedelta(
                days=today.weekday()
            )  # Monday of current week

        schedules = Schedule.objects.filter(teacher=self, is_recurring=True)
        week_schedule = {}

        for i in range(7):  # 7 days
            day_date = week_start + timedelta(days=i)
            day_name = day_date.strftime("%A")  # e.g., 'Monday'

            # Find schedules for this day that are active
            active_schedules = []
            for schedule in schedules.filter(day_of_week=day_name):
                if schedule.is_active_on_date(day_date):
                    active_schedules.append(
                        {
                            "group": schedule.group.name,
                            "start_time": schedule.start_time,
                            "end_time": schedule.end_time,
                            "course": (
                                schedule.group.current_course.title
                                if schedule.group.current_course
                                else None
                            ),
                            "lesson": (
                                schedule.group.current_lesson.title
                                if schedule.group.current_lesson
                                else None
                            ),
                        }
                    )

            week_schedule[day_name] = active_schedules

        return week_schedule


class Schedule(models.Model):
    """
    Model for recurring weekly teaching schedules linked to groups and teachers.
    Supports 3 lessons per week by creating separate instances for each lesson day.
    """

    DAY_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    ]

    group = models.ForeignKey(
        "Group",
        on_delete=models.CASCADE,
        related_name="schedules",
        help_text="Group being taught in this schedule",
    )
    teacher = models.ForeignKey(
        "Teacher",
        on_delete=models.CASCADE,
        related_name="schedules",
        help_text="Teacher assigned to this schedule",
    )
    day_of_week = models.CharField(
        max_length=10,
        choices=DAY_CHOICES,
        help_text="Day of the week for this recurring lesson",
    )
    start_time = models.TimeField(help_text="Start time of the lesson")
    end_time = models.TimeField(help_text="End time of the lesson")
    start_date = models.DateField(help_text="Start date of the recurring schedule")
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional manual override for end date (leave blank to use course duration)",
    )
    is_recurring = models.BooleanField(
        default=True, help_text="True for weekly recurring schedules"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this schedule is currently active"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_schedule"
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"
        ordering = ["day_of_week", "start_time"]
        unique_together = ("group", "teacher", "day_of_week", "start_time")

    def clean(self):
        """Validate that teacher is assigned to the group and times are logical"""
        if self.teacher not in self.group.teachers.all():
            raise ValidationError("Teacher must be assigned to the group.")

        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

    def __str__(self):
        return f"{self.teacher} - {self.group} every {self.day_of_week} ({self.start_time}-{self.end_time})"

    @property
    def calculated_end_date(self):
        """
        Calculates the end date based on the group's course duration.
        Returns manual end_date if set, otherwise calculates from course duration.
        """
        if self.end_date:
            return self.end_date

        if self.group.current_course and self.group.current_course.duration_weeks:
            return self.start_date + timedelta(
                weeks=self.group.current_course.duration_weeks
            )

        return None  # Open-ended if no course or duration

    def is_active_on_date(self, date):
        """
        Check if this schedule is active on a specific date.
        Returns True if the date falls within the schedule's active period.
        """
        if not self.is_active:
            return False

        if date < self.start_date:
            return False

        end_date = self.calculated_end_date
        if end_date and date > end_date:
            return False

        return True

    def get_remaining_weeks(self):
        """Returns the number of weeks remaining in this schedule"""
        from django.utils import timezone

        end_date = self.calculated_end_date
        if not end_date:
            return None

        today = timezone.now().date()
        if today > end_date:
            return 0

        return (end_date - today).days // 7


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
    
    # Admin-only notes field
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes for admin use only - not visible to students",
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
