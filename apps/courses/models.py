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
        'accounts.Teacher',
        related_name='lessons',
        blank=True,
        help_text="Teachers who can teach this lesson"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_lessons'
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    @property
    def teacher_names(self):
        """Return comma-separated list of teacher names."""
        return ", ".join([teacher.full_name for teacher in self.teachers.all()])
    
    def get_homework_count(self):
        """Return the number of homework assignments for this lesson."""
        return self.homework_set.count()
