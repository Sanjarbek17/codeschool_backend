from django.db import models


class Homework(models.Model):
    """
    Homework model representing assignments related to specific lessons.
    Contains homework information and relationships to lessons.
    """
    lesson = models.ForeignKey(
        'courses.Lessons',
        on_delete=models.CASCADE,
        related_name='homework_set',
        help_text="The lesson this homework belongs to"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Homework description and instructions")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignments_homework'
        verbose_name = 'Homework'
        verbose_name_plural = 'Homework'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
    
    def get_task_count(self):
        """Return the number of tasks in this homework."""
        return self.tasks.count()
    
    def get_completion_rate(self):
        """Calculate overall completion rate for this homework."""
        from apps.progress.models import HomeworkProgress
        total_students = HomeworkProgress.objects.filter(homework=self).count()
        completed_students = HomeworkProgress.objects.filter(
            homework=self, 
            is_completed=True
        ).count()
        
        if total_students == 0:
            return 0
        return (completed_students / total_students) * 100


class Task(models.Model):
    """
    Task model representing individual tasks within homework assignments.
    Each task can have test cases and submissions.
    """
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="The homework this task belongs to"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Task description and requirements")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignments_task'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['homework', 'created_at']

    def __str__(self):
        return f"{self.homework.title} - {self.title}"
    
    def get_test_case_count(self):
        """Return the number of test cases for this task."""
        from apps.submissions.models import TestCase
        return TestCase.objects.filter(task=self).count()
    
    def get_submission_count(self):
        """Return the number of submissions for this task."""
        from apps.submissions.models import HomeworkSubmission
        return HomeworkSubmission.objects.filter(task=self).count()
