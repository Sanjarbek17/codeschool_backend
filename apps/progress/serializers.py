from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Max
from .models import HomeworkProgress, TaskProgress

User = get_user_model()


class StudentBasicSerializer(serializers.ModelSerializer):
    """Basic student information for progress tracking."""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        from apps.accounts.models import Student
        model = Student
        fields = ['id', 'full_name', 'username']


class HomeworkBasicSerializer(serializers.Serializer):
    """Basic homework information for progress tracking."""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_id = serializers.IntegerField(source='lesson.id', read_only=True)


class TaskBasicSerializer(serializers.Serializer):
    """Basic task information for progress tracking."""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    homework_id = serializers.IntegerField(source='homework.id', read_only=True)


class HomeworkProgressSerializer(serializers.ModelSerializer):
    """Complete serializer for homework progress with detailed information."""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.user.username', read_only=True)
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    lesson_title = serializers.CharField(source='homework.lesson.title', read_only=True)
    lesson_id = serializers.IntegerField(source='homework.lesson.id', read_only=True)
    completion_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = HomeworkProgress
        fields = [
            'id', 'homework', 'student', 'student_name', 'student_username',
            'homework_title', 'lesson_title', 'lesson_id',
            'total_tasks', 'solved_tasks', 'completion_percentage',
            'is_completed', 'last_attempt_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class HomeworkProgressListSerializer(serializers.ModelSerializer):
    """Simplified serializer for homework progress lists."""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    completion_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = HomeworkProgress
        fields = [
            'id', 'student_name', 'homework_title', 'total_tasks', 'solved_tasks',
            'completion_percentage', 'is_completed', 'last_attempt_at'
        ]


class HomeworkProgressCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating homework progress."""
    
    class Meta:
        model = HomeworkProgress
        fields = ['homework', 'student', 'total_tasks', 'solved_tasks', 'last_attempt_at']
    
    def create(self, validated_data):
        """Create homework progress with automatic completion status update."""
        progress = super().create(validated_data)
        progress.update_completion_status()
        return progress
    
    def update(self, instance, validated_data):
        """Update homework progress with automatic completion status update."""
        progress = super().update(instance, validated_data)
        progress.update_completion_status()
        return progress


class TaskProgressSerializer(serializers.ModelSerializer):
    """Complete serializer for task progress with detailed information."""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.user.username', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    homework_title = serializers.CharField(source='task.homework.title', read_only=True)
    lesson_title = serializers.CharField(source='task.homework.lesson.title', read_only=True)
    test_pass_percentage = serializers.ReadOnlyField()
    last_submission_id = serializers.IntegerField(source='last_submission.id', read_only=True)
    
    class Meta:
        model = TaskProgress
        fields = [
            'id', 'task', 'student', 'student_name', 'student_username',
            'task_title', 'homework_title', 'lesson_title',
            'is_solved', 'best_passed_tests', 'total_tests', 'test_pass_percentage',
            'last_attempt_at', 'last_submission_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TaskProgressListSerializer(serializers.ModelSerializer):
    """Simplified serializer for task progress lists."""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    test_pass_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = TaskProgress
        fields = [
            'id', 'student_name', 'task_title', 'is_solved',
            'best_passed_tests', 'total_tests', 'test_pass_percentage', 'last_attempt_at'
        ]


class TaskProgressCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating task progress."""
    
    class Meta:
        model = TaskProgress
        fields = [
            'task', 'student', 'best_passed_tests', 'total_tests',
            'last_attempt_at', 'last_submission'
        ]
    
    def create(self, validated_data):
        """Create task progress with automatic solved status update."""
        progress = super().create(validated_data)
        progress.update_solved_status()
        return progress
    
    def update(self, instance, validated_data):
        """Update task progress with automatic solved status update."""
        progress = super().update(instance, validated_data)
        progress.update_solved_status()
        return progress


class StudentProgressSummarySerializer(serializers.Serializer):
    """Serializer for student progress summary across all homework."""
    student = StudentBasicSerializer()
    total_homework = serializers.IntegerField()
    completed_homework = serializers.IntegerField()
    homework_completion_rate = serializers.FloatField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    task_completion_rate = serializers.FloatField()
    average_task_score = serializers.FloatField()
    last_activity = serializers.DateTimeField()
    recent_homework = HomeworkProgressListSerializer(many=True)


class TeacherProgressDashboardSerializer(serializers.Serializer):
    """Serializer for teacher progress dashboard with lesson statistics."""
    lesson_id = serializers.IntegerField()
    lesson_title = serializers.CharField()
    total_students = serializers.IntegerField()
    total_homework = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    average_homework_completion = serializers.FloatField()
    average_task_completion = serializers.FloatField()
    active_students = serializers.IntegerField()
    recent_activity = serializers.DateTimeField()


class LessonProgressAnalyticsSerializer(serializers.Serializer):
    """Detailed analytics for lesson progress."""
    lesson = serializers.DictField()
    overview = serializers.DictField()
    homework_breakdown = serializers.ListField()
    student_rankings = serializers.ListField()
    difficulty_analysis = serializers.ListField()
    time_trends = serializers.ListField()


class HomeworkAnalyticsSerializer(serializers.Serializer):
    """Detailed analytics for specific homework progress."""
    homework = HomeworkBasicSerializer()
    overview = serializers.DictField()
    task_breakdown = serializers.ListField()
    student_progress = serializers.ListField()
    completion_timeline = serializers.ListField()
    difficulty_metrics = serializers.DictField()


class StudentAnalyticsSerializer(serializers.Serializer):
    """Comprehensive analytics for individual student progress."""
    student = StudentBasicSerializer()
    overall_stats = serializers.DictField()
    homework_progress = serializers.ListField()
    task_performance = serializers.ListField()
    learning_trends = serializers.DictField()
    strengths_weaknesses = serializers.DictField()


class ProgressComparisonSerializer(serializers.Serializer):
    """Serializer for comparing progress between students or time periods."""
    comparison_type = serializers.CharField()
    baseline = serializers.DictField()
    comparison = serializers.DictField()
    metrics = serializers.DictField()
    improvements = serializers.ListField()
    areas_for_focus = serializers.ListField()


class LearningPathSerializer(serializers.Serializer):
    """Serializer for suggested learning paths based on progress."""
    student = StudentBasicSerializer()
    current_level = serializers.DictField()
    suggested_tasks = serializers.ListField()
    skill_gaps = serializers.ListField()
    recommended_resources = serializers.ListField()
    estimated_completion_time = serializers.IntegerField()


class ProgressInsightsSerializer(serializers.Serializer):
    """AI-powered insights from progress data."""
    insights_type = serializers.CharField()
    key_findings = serializers.ListField()
    recommendations = serializers.ListField()
    predicted_outcomes = serializers.DictField()
    risk_factors = serializers.ListField()
    success_patterns = serializers.ListField()
