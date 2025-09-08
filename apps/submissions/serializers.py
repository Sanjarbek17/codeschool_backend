from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import HomeworkSubmission, TestCase

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for student information in submissions."""

    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        from apps.accounts.models import Student

        model = Student
        fields = ["id", "full_name", "username"]


class TaskBasicSerializer(serializers.Serializer):
    """Basic task information for submissions."""

    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    homework_title = serializers.CharField(source="homework.title", read_only=True)
    lesson_title = serializers.CharField(source="homework.lesson.title", read_only=True)


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    """Complete serializer for homework submissions with all details."""

    student_name = serializers.CharField(
        source="student.user.get_full_name", read_only=True
    )
    student_username = serializers.CharField(
        source="student.user.username", read_only=True
    )
    task_title = serializers.CharField(source="task.title", read_only=True)
    homework_title = serializers.CharField(source="task.homework.title", read_only=True)
    lesson_title = serializers.CharField(
        source="task.homework.lesson.title", read_only=True
    )
    success_rate = serializers.ReadOnlyField()
    is_successful = serializers.ReadOnlyField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = HomeworkSubmission
        fields = [
            "id",
            "task",
            "student",
            "student_name",
            "student_username",
            "task_title",
            "homework_title",
            "lesson_title",
            "code_text",
            "file_upload",
            "submitted_at",
            "passed_tests",
            "total_tests",
            "success_rate",
            "is_successful",
            "execution_time",
            "memory_usage",
            "file_size",
        ]
        read_only_fields = [
            "submitted_at",
            "passed_tests",
            "total_tests",
            "execution_time",
            "memory_usage",
        ]

    def get_file_size(self, obj):
        """Get file size in human readable format."""
        size_bytes = obj.get_file_size()
        if size_bytes == 0:
            return None

        # Convert to human readable format
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"


class HomeworkSubmissionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for submission lists."""

    student_name = serializers.CharField(
        source="student.user.get_full_name", read_only=True
    )
    task_title = serializers.CharField(source="task.title", read_only=True)
    success_rate = serializers.ReadOnlyField()
    is_successful = serializers.ReadOnlyField()

    class Meta:
        model = HomeworkSubmission
        fields = [
            "id",
            "student_name",
            "task_title",
            "submitted_at",
            "passed_tests",
            "total_tests",
            "success_rate",
            "is_successful",
        ]


class HomeworkSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new submissions."""

    auto_test = serializers.BooleanField(
        default=True,
        write_only=True,
        required=False,
        help_text="Whether to automatically run tests on submission",
    )

    class Meta:
        model = HomeworkSubmission
        fields = ["task", "code_text", "file_upload", "auto_test"]

    def validate(self, data):
        """Validate that either code_text or file_upload is provided."""
        if not data.get("code_text") and not data.get("file_upload"):
            raise serializers.ValidationError(
                "Either code_text or file_upload must be provided."
            )
        return data

    def create(self, validated_data):
        """Create submission with current user as student."""
        request = self.context["request"]
        validated_data["student"] = request.user.student

        # Remove auto_test from validated_data as it's not a model field
        auto_test = validated_data.pop("auto_test", True)

        # Get test case count for the task
        from .models import TestCase

        task = validated_data["task"]
        total_tests = TestCase.get_total_count(task)
        validated_data["total_tests"] = total_tests

        return super().create(validated_data)


class HomeworkSubmissionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating submissions (admin/teacher only)."""

    class Meta:
        model = HomeworkSubmission
        fields = ["passed_tests", "total_tests", "execution_time", "memory_usage"]

    def validate_passed_tests(self, value):
        """Validate that passed_tests doesn't exceed total_tests."""
        total_tests = self.instance.total_tests
        if hasattr(self, "initial_data") and "total_tests" in self.initial_data:
            total_tests = self.initial_data["total_tests"]

        if value > total_tests:
            raise serializers.ValidationError("Passed tests cannot exceed total tests.")
        return value


class TestCaseSerializer(serializers.ModelSerializer):
    """Complete serializer for test cases."""

    task_title = serializers.CharField(source="task.title", read_only=True)
    homework_title = serializers.CharField(source="task.homework.title", read_only=True)

    class Meta:
        model = TestCase
        fields = [
            "id",
            "task",
            "task_title",
            "homework_title",
            "test_code",
            "hidden",
            "input_data",
            "expected_output",
            "timeout_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TestCaseListSerializer(serializers.ModelSerializer):
    """Simplified serializer for test case lists."""

    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = TestCase
        fields = ["id", "task_title", "hidden", "timeout_seconds", "created_at"]


class TestCaseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating test cases."""

    class Meta:
        model = TestCase
        fields = [
            "task",
            "test_code",
            "hidden",
            "input_data",
            "expected_output",
            "timeout_seconds",
        ]


class TestCaseStudentSerializer(serializers.ModelSerializer):
    """Serializer for test cases visible to students (hides sensitive data)."""

    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = TestCase
        fields = [
            "id",
            "task_title",
            "input_data",
            "expected_output",
            "timeout_seconds",
        ]

    def to_representation(self, instance):
        """Hide test_code and sensitive data for hidden test cases."""
        data = super().to_representation(instance)

        # If it's a hidden test case, hide the sensitive information
        if instance.hidden:
            data["input_data"] = "Hidden"
            data["expected_output"] = "Hidden"

        return data


class SubmissionStatisticsSerializer(serializers.Serializer):
    """Serializer for submission statistics."""

    task_title = serializers.CharField()
    homework_title = serializers.CharField()
    lesson_title = serializers.CharField()
    total_submissions = serializers.IntegerField()
    successful_submissions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    average_execution_time = serializers.FloatField()
    average_memory_usage = serializers.FloatField()
    latest_submission = serializers.DateTimeField()


class StudentProgressSerializer(serializers.Serializer):
    """Serializer for individual student progress."""

    student_name = serializers.CharField()
    student_username = serializers.CharField()
    task_title = serializers.CharField()
    homework_title = serializers.CharField()
    total_submissions = serializers.IntegerField()
    best_score = serializers.FloatField()
    is_completed = serializers.BooleanField()
    latest_submission = serializers.DateTimeField()
    execution_time = serializers.FloatField()
    memory_usage = serializers.IntegerField()


class TaskAnalyticsSerializer(serializers.Serializer):
    """Serializer for detailed task analytics."""

    task = TaskBasicSerializer()
    total_students = serializers.IntegerField()
    submitted_students = serializers.IntegerField()
    completed_students = serializers.IntegerField()
    submission_rate = serializers.FloatField()
    completion_rate = serializers.FloatField()
    average_attempts = serializers.FloatField()
    average_success_rate = serializers.FloatField()
    difficulty_score = serializers.FloatField()
    student_progress = StudentProgressSerializer(many=True)
