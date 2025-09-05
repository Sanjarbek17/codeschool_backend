from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Max, Q, F
from django.utils import timezone
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import HomeworkSubmission, TestCase
from .serializers import (
    HomeworkSubmissionSerializer,
    HomeworkSubmissionListSerializer,
    HomeworkSubmissionCreateSerializer,
    HomeworkSubmissionUpdateSerializer,
    TestCaseSerializer,
    TestCaseListSerializer,
    TestCaseCreateSerializer,
    TestCaseStudentSerializer,
    SubmissionStatisticsSerializer,
    StudentProgressSerializer,
    TaskAnalyticsSerializer,
)
from apps.accounts.permissions import (
    IsTeacherOrAdmin,
    IsStudentOwnerOrTeacherOrAdmin,
    IsAssignedTeacherOrAdmin,
    IsStudentOrAdmin,
)

User = get_user_model()


class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing homework submissions.

    - Students can create and view their own submissions
    - Teachers can view submissions for their assigned lessons
    - Admins have full access
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(tags=["Submissions"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Filter submissions based on user role."""
        user = self.request.user

        if user.is_superuser:
            # Admins see all submissions
            return (
                HomeworkSubmission.objects.all()
                .select_related("student__user", "task__homework__lesson")
                .prefetch_related("task__homework__lesson__teachers")
            )

        elif hasattr(user, "teacher"):
            # Teachers see submissions for their assigned lessons
            return (
                HomeworkSubmission.objects.filter(
                    task__homework__lesson__teachers=user.teacher
                )
                .select_related("student__user", "task__homework__lesson")
                .prefetch_related("task__homework__lesson__teachers")
            )

        elif hasattr(user, "student"):
            # Students see only their own submissions
            return (
                HomeworkSubmission.objects.filter(student=user.student)
                .select_related("student__user", "task__homework__lesson")
                .prefetch_related("task__homework__lesson__teachers")
            )

        return HomeworkSubmission.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return HomeworkSubmissionListSerializer
        elif self.action == "create":
            return HomeworkSubmissionCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return HomeworkSubmissionUpdateSerializer
        return HomeworkSubmissionSerializer

    def get_permissions(self):
        """Get permissions based on action."""
        if self.action == "create":
            # Only students can create submissions
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only teachers/admins can update submissions
            permission_classes = [IsTeacherOrAdmin]
        else:
            # View permissions handled in get_queryset
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """Create a new submission (students only)."""
        if not hasattr(request.user, "student"):
            return Response(
                {"error": "Only students can create submissions"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def my_submissions(self, request):
        """Get current student's submissions."""
        if not hasattr(request.user, "student"):
            return Response(
                {"error": "Only students can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN,
            )

        submissions = self.get_queryset().filter(student=request.user.student)

        # Optional filtering
        task_id = request.query_params.get("task")
        if task_id:
            submissions = submissions.filter(task_id=task_id)

        serializer = HomeworkSubmissionListSerializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Get submission statistics for teachers."""
        if not hasattr(request.user, "teacher") and not request.user.is_superuser:
            return Response(
                {"error": "Only teachers can access statistics"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get submissions for teacher's lessons
        submissions = self.get_queryset()

        # Optional filtering by lesson or homework
        lesson_id = request.query_params.get("lesson")
        homework_id = request.query_params.get("homework")

        if lesson_id:
            submissions = submissions.filter(task__homework__lesson_id=lesson_id)
        if homework_id:
            submissions = submissions.filter(task__homework_id=homework_id)

        # Calculate statistics
        stats_data = submissions.values(
            "task__title", "task__homework__title", "task__homework__lesson__title"
        ).annotate(
            total_submissions=Count("id"),
            successful_submissions=Count(
                "id", filter=Q(passed_tests__gte=F("total_tests"))
            ),
            average_execution_time=Avg("execution_time"),
            average_memory_usage=Avg("memory_usage"),
            latest_submission=Max("submitted_at"),
        )

        # Add success rate calculation
        for stat in stats_data:
            total = stat["total_submissions"]
            successful = stat["successful_submissions"]
            stat["success_rate"] = (successful / total * 100) if total > 0 else 0

        serializer = SubmissionStatisticsSerializer(stats_data, many=True)
        return Response(
            {"teacher": request.user.get_full_name(), "statistics": serializer.data}
        )

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk=None):
        """Evaluate a submission (teachers/admins only)."""
        if not hasattr(request.user, "teacher") and not request.user.is_superuser:
            return Response(
                {"error": "Only teachers can evaluate submissions"},
                status=status.HTTP_403_FORBIDDEN,
            )

        submission = self.get_object()

        # Update evaluation results
        passed_tests = request.data.get("passed_tests")
        execution_time = request.data.get("execution_time")
        memory_usage = request.data.get("memory_usage")

        if passed_tests is not None:
            if passed_tests > submission.total_tests:
                return Response(
                    {"error": "Passed tests cannot exceed total tests"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            submission.passed_tests = passed_tests

        if execution_time is not None:
            submission.execution_time = execution_time

        if memory_usage is not None:
            submission.memory_usage = memory_usage

        submission.save()

        serializer = HomeworkSubmissionSerializer(submission)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def task_analytics(self, request):
        """Get detailed analytics for tasks (teachers only)."""
        if not hasattr(request.user, "teacher") and not request.user.is_superuser:
            return Response(
                {"error": "Only teachers can access analytics"},
                status=status.HTTP_403_FORBIDDEN,
            )

        task_id = request.query_params.get("task")
        if not task_id:
            return Response(
                {"error": "task parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.assignments.models import Task

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if teacher has access to this task
        if hasattr(request.user, "teacher") and not request.user.is_superuser:
            if not task.homework.lesson.teachers.filter(
                id=request.user.teacher.id
            ).exists():
                return Response(
                    {"error": "You do not have access to this task"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Get all students for the lesson
        from apps.progress.models import StudentProgress

        lesson_students = StudentProgress.objects.filter(
            lesson=task.homework.lesson
        ).values_list("student", flat=True)

        total_students = len(lesson_students)

        # Get submissions for this task
        submissions = HomeworkSubmission.objects.filter(
            task=task, student__in=lesson_students
        )

        # Calculate metrics
        submitted_students = submissions.values("student").distinct().count()
        completed_students = (
            submissions.filter(passed_tests__gte=F("total_tests"))
            .values("student")
            .distinct()
            .count()
        )

        submission_rate = (
            (submitted_students / total_students * 100) if total_students > 0 else 0
        )
        completion_rate = (
            (completed_students / total_students * 100) if total_students > 0 else 0
        )

        # Student progress details
        student_progress = []
        for student_id in lesson_students:
            student_submissions = submissions.filter(student_id=student_id)
            if student_submissions.exists():
                best_submission = student_submissions.order_by(
                    "-passed_tests", "submitted_at"
                ).first()
                latest_submission = student_submissions.order_by(
                    "-submitted_at"
                ).first()

                student_progress.append(
                    {
                        "student_name": best_submission.student.user.get_full_name(),
                        "student_username": best_submission.student.user.username,
                        "task_title": task.title,
                        "homework_title": task.homework.title,
                        "total_submissions": student_submissions.count(),
                        "best_score": best_submission.success_rate,
                        "is_completed": best_submission.is_successful,
                        "latest_submission": latest_submission.submitted_at,
                        "execution_time": best_submission.execution_time or 0,
                        "memory_usage": best_submission.memory_usage or 0,
                    }
                )

        # Calculate difficulty score (inverse of completion rate)
        difficulty_score = max(0, 100 - completion_rate)

        # Calculate average attempts
        student_attempts = (
            submissions.values("student")
            .annotate(attempts=Count("id"))
            .values_list("attempts", flat=True)
        )
        average_attempts = (
            sum(student_attempts) / len(student_attempts) if student_attempts else 0
        )

        # Calculate average success rate
        success_rates = [s["best_score"] for s in student_progress]
        average_success_rate = (
            sum(success_rates) / len(success_rates) if success_rates else 0
        )

        analytics_data = {
            "task": {
                "id": task.id,
                "title": task.title,
                "homework_title": task.homework.title,
                "lesson_title": task.homework.lesson.title,
            },
            "total_students": total_students,
            "submitted_students": submitted_students,
            "completed_students": completed_students,
            "submission_rate": submission_rate,
            "completion_rate": completion_rate,
            "average_attempts": average_attempts,
            "average_success_rate": average_success_rate,
            "difficulty_score": difficulty_score,
            "student_progress": student_progress,
        }

        serializer = TaskAnalyticsSerializer(analytics_data)
        return Response(serializer.data)


class TestCaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing test cases.

    - Teachers can create and manage test cases for their lessons
    - Students can view non-hidden test cases
    - Admins have full access
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(tags=["Submissions"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Submissions"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Filter test cases based on user role."""
        user = self.request.user

        if user.is_superuser:
            # Admins see all test cases
            return TestCase.objects.all().select_related("task__homework__lesson")

        elif hasattr(user, "teacher"):
            # Teachers see test cases for their assigned lessons
            return TestCase.objects.filter(
                task__homework__lesson__teachers=user.teacher
            ).select_related("task__homework__lesson")

        elif hasattr(user, "student"):
            # Students see only non-hidden test cases for lessons they're enrolled in
            from apps.progress.models import StudentProgress

            enrolled_lessons = StudentProgress.objects.filter(
                student=user.student
            ).values_list("lesson", flat=True)

            return TestCase.objects.filter(
                task__homework__lesson__in=enrolled_lessons, hidden=False
            ).select_related("task__homework__lesson")

        return TestCase.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on action and user role."""
        user = self.request.user

        if self.action == "list":
            return TestCaseListSerializer
        elif self.action == "create":
            return TestCaseCreateSerializer
        elif hasattr(user, "student"):
            # Students get filtered view
            return TestCaseStudentSerializer
        return TestCaseSerializer

    def get_permissions(self):
        """Get permissions based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only teachers/admins can modify test cases
            permission_classes = [IsTeacherOrAdmin]
        else:
            # View permissions handled in get_queryset
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def task_test_cases(self, request):
        """Get test cases for a specific task."""
        task_id = request.query_params.get("task")
        if not task_id:
            return Response(
                {"error": "task parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        test_cases = self.get_queryset().filter(task_id=task_id)
        serializer = self.get_serializer(test_cases, many=True)

        # Additional task information
        if test_cases.exists():
            first_test_case = test_cases.first()
            return Response(
                {
                    "task": first_test_case.task.title,
                    "homework": first_test_case.task.homework.title,
                    "lesson": first_test_case.task.homework.lesson.title,
                    "test_case_count": test_cases.count(),
                    "test_cases": serializer.data,
                }
            )

        return Response({"test_case_count": 0, "test_cases": []})
