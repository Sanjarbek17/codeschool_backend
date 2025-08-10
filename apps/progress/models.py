from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class HomeworkProgress(models.Model):
    """
    HomeworkProgress model tracking student progress on homework assignments.
    Tracks completion status and progress metrics.
    """
    homework = models.ForeignKey(
        'assignments.Homework',
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='homework_progress'
    )
    total_tasks = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Total number of tasks in this homework"
    )
    solved_tasks = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of tasks completed by the student"
    )
    is_completed = models.BooleanField(
        default=False,
        help_text="Whether the homework is fully completed"
    )
    last_attempt_at = models.DateTimeField(
        help_text="When the student last worked on this homework"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'progress_homework_progress'
        verbose_name = 'Homework Progress'
        verbose_name_plural = 'Homework Progress'
        unique_together = ('homework', 'student')
        ordering = ['-last_attempt_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.homework.title} ({self.solved_tasks}/{self.total_tasks})"
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage."""
        if self.total_tasks == 0:
            return 0
        return (self.solved_tasks / self.total_tasks) * 100
    
    def update_completion_status(self):
        """Update is_completed based on solved vs total tasks."""
        self.is_completed = self.solved_tasks >= self.total_tasks
        self.save(update_fields=['is_completed'])


class TaskProgress(models.Model):
    """
    TaskProgress model tracking student progress on individual tasks.
    Tracks test case performance and completion status.
    """
    task = models.ForeignKey(
        'assignments.Task',
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='task_progress'
    )
    is_solved = models.BooleanField(
        default=False,
        help_text="Whether the task is completed successfully"
    )
    best_passed_tests = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        help_text="Highest number of test cases passed"
    )
    total_tests = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Total number of test cases for this task"
    )
    last_attempt_at = models.DateTimeField(
        help_text="When the student last attempted this task"
    )
    last_submission = models.ForeignKey(
        'submissions.HomeworkSubmission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='progress_records',
        help_text="Reference to the most recent submission"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'progress_task_progress'
        verbose_name = 'Task Progress'
        verbose_name_plural = 'Task Progress'
        unique_together = ('task', 'student')
        ordering = ['-last_attempt_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.task.title} ({self.best_passed_tests}/{self.total_tests})"
    
    @property
    def test_pass_percentage(self):
        """Calculate test case pass percentage."""
        if self.total_tests == 0:
            return 0
        return (self.best_passed_tests / self.total_tests) * 100
    
    def update_solved_status(self):
        """Update is_solved based on test performance."""
        self.is_solved = self.best_passed_tests >= self.total_tests
        self.save(update_fields=['is_solved'])
