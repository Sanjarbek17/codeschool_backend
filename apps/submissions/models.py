from django.db import models
from django.core.validators import MinValueValidator


class HomeworkSubmission(models.Model):
    """
    HomeworkSubmission model representing student code submissions for tasks.
    Supports both text code and file uploads with test result tracking.
    """
    task = models.ForeignKey(
        'assignments.Task',
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="The task this submission is for"
    )
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="The student who made this submission"
    )
    code_text = models.TextField(
        help_text="The submitted code as text"
    )
    file_upload = models.FileField(
        upload_to='submissions/',
        null=True,
        blank=True,
        help_text="Optional file upload for the submission"
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this submission was made"
    )
    passed_tests = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        help_text="Number of test cases passed by this submission"
    )
    total_tests = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Total number of test cases for this task"
    )
    
    # Additional metadata
    execution_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Execution time in seconds (if measured)"
    )
    memory_usage = models.IntegerField(
        null=True,
        blank=True,
        help_text="Memory usage in KB (if measured)"
    )
    
    class Meta:
        db_table = 'submissions_homework_submission'
        verbose_name = 'Homework Submission'
        verbose_name_plural = 'Homework Submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['task', 'student']),
            models.Index(fields=['submitted_at']),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.task.title} ({self.passed_tests}/{self.total_tests})"
    
    @property
    def success_rate(self):
        """Calculate the success rate of this submission."""
        if self.total_tests == 0:
            return 0
        return (self.passed_tests / self.total_tests) * 100
    
    @property
    def is_successful(self):
        """Check if this submission passed all tests."""
        return self.passed_tests >= self.total_tests
    
    def get_file_size(self):
        """Get the size of uploaded file in bytes."""
        if self.file_upload:
            return self.file_upload.size
        return 0


class TestCase(models.Model):
    """
    TestCase model representing test cases for automated code evaluation.
    Can be hidden from students to prevent gaming the system.
    """
    task = models.ForeignKey(
        'assignments.Task',
        on_delete=models.CASCADE,
        related_name='test_cases',
        help_text="The task this test case belongs to"
    )
    test_code = models.TextField(
        help_text="The test code to execute for validation"
    )
    hidden = models.BooleanField(
        default=False,
        help_text="Whether this test case is hidden from students"
    )
    
    # Test case metadata
    input_data = models.TextField(
        blank=True,
        help_text="Input data for the test case"
    )
    expected_output = models.TextField(
        blank=True,
        help_text="Expected output for the test case"
    )
    timeout_seconds = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Maximum execution time allowed for this test"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'submissions_test_case'
        verbose_name = 'Test Case'
        verbose_name_plural = 'Test Cases'
        ordering = ['task', 'hidden', 'created_at']
        indexes = [
            models.Index(fields=['task', 'hidden']),
        ]

    def __str__(self):
        visibility = "Hidden" if self.hidden else "Visible"
        return f"{self.task.title} - Test Case ({visibility})"
    
    @classmethod
    def get_visible_count(cls, task):
        """Get count of visible test cases for a task."""
        return cls.objects.filter(task=task, hidden=False).count()
    
    @classmethod
    def get_total_count(cls, task):
        """Get total count of test cases for a task."""
        return cls.objects.filter(task=task).count()
