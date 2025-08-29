from django.db import models


class Lessons(models.Model):
    """
    Lessons model representing academic content and learning materials.
    Can be taught by multiple teachers (many-to-many relationship).
    """

    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField(blank=True, null=True, help_text="URL to lesson video")
    content = models.TextField(help_text="Lesson content and materials")

    # Many-to-many relationship with teachers
    teachers = models.ManyToManyField(
        "accounts.Teacher",
        related_name="lessons",
        blank=True,
        help_text="Teachers who can teach this lesson",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses_lessons"
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def teacher_names(self):
        """Return comma-separated list of teacher names."""
        return ", ".join([teacher.full_name for teacher in self.teachers.all()])

    def get_homework_count(self):
        """Return the number of homework assignments for this lesson."""
        return self.homework_set.count()


class Attendance(models.Model):
    """
    Attendance model for tracking student attendance in lessons.
    Teachers can mark attendance for students in their groups for specific lessons.
    """

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused"),
    ]

    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="attendances",
        help_text="Student whose attendance is being tracked",
    )
    lesson = models.ForeignKey(
        Lessons,
        on_delete=models.CASCADE,
        related_name="attendances",
        help_text="Lesson for which attendance is being tracked",
    )
    group = models.ForeignKey(
        "accounts.Group",
        on_delete=models.CASCADE,
        related_name="attendances",
        help_text="Group in which the lesson was conducted",
    )
    teacher = models.ForeignKey(
        "accounts.Teacher",
        on_delete=models.CASCADE,
        related_name="recorded_attendances",
        help_text="Teacher who recorded the attendance",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="present")
    date = models.DateField(help_text="Date of the lesson")
    notes = models.TextField(blank=True, help_text="Additional notes about attendance")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses_attendance"
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"
        ordering = ["-date", "-created_at"]
        # Ensure unique attendance record per student, lesson, group, and date
        unique_together = ["student", "lesson", "group", "date"]

    def __str__(self):
        return f"{self.student.full_name} - {self.lesson.title} - {self.get_status_display()} ({self.date})"

    @property
    def is_present(self):
        """Returns True if student was present or late"""
        return self.status in ["present", "late"]

    def save(self, *args, **kwargs):
        """Override save to ensure the student belongs to the group"""
        if self.student not in self.group.students.all():
            raise ValueError(
                f"Student {self.student} is not enrolled in group {self.group}"
            )
        if self.teacher not in self.group.teachers.all():
            raise ValueError(
                f"Teacher {self.teacher} is not assigned to group {self.group}"
            )
        super().save(*args, **kwargs)
