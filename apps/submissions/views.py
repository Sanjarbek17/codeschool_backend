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
from apps.editor.services import AutomatedTestRunner

User = get_user_model()


class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing homework submissions.

    - Students can create and view their own submissions
    - Teachers can view submissions for their assigned lessons
    - Admins have full access
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List homework submissions with filtering based on user role",
        operation_summary="List Submissions",
        tags=["Submissions"],
        responses={200: HomeworkSubmissionListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new homework submission (students only)",
        operation_summary="Create Submission",
        tags=["Submissions"],
        request_body=HomeworkSubmissionCreateSerializer,
        responses={201: HomeworkSubmissionSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve detailed submission information",
        operation_summary="Get Submission Detail",
        tags=["Submissions"],
        responses={200: HomeworkSubmissionSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a submission (teachers/admins only)",
        operation_summary="Update Submission",
        tags=["Submissions"],
        request_body=HomeworkSubmissionUpdateSerializer,
        responses={200: HomeworkSubmissionSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a submission (teachers/admins only)",
        operation_summary="Partially Update Submission",
        tags=["Submissions"],
        request_body=HomeworkSubmissionUpdateSerializer,
        responses={200: HomeworkSubmissionSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a submission (teachers/admins only)",
        operation_summary="Delete Submission",
        tags=["Submissions"],
        responses={204: "Submission deleted successfully"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

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

        elif hasattr(user, "teacher_profile"):
            # Teachers see submissions for their assigned lessons
            return (
                HomeworkSubmission.objects.filter(
                    task__homework__lesson__teachers=user.teacher_profile
                )
                .select_related("student__user", "task__homework__lesson")
                .prefetch_related("task__homework__lesson__teachers")
            )

        elif hasattr(user, "student_profile"):
            # Students see only their own submissions
            return (
                HomeworkSubmission.objects.filter(student=user.student_profile)
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
        """Create a new submission with automatic testing and update progress."""
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Only students can create submissions"},
                status=status.HTTP_403_FORBIDDEN,
            )

        from apps.progress.models import HomeworkProgress, TaskProgress
        from django.utils import timezone

        # Create the submission first
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()

        # Check if auto-testing is enabled and code is provided
        auto_test = request.data.get("auto_test", True)  # Default to True

        if auto_test and submission.code_text:
            try:
                # Run automated tests
                test_runner = AutomatedTestRunner()
                test_results = test_runner.evaluate_and_update_submission(submission)

                # Refresh submission from database to get updated values
                submission.refresh_from_db()

                # --- Progress Tracking Logic ---
                student = submission.student
                task = submission.task
                homework = task.homework

                # HomeworkProgress
                homework_progress, _ = HomeworkProgress.objects.get_or_create(
                    homework=homework,
                    student=student,
                    defaults={
                        "total_tasks": homework.tasks.count(),
                        "solved_tasks": 0,
                        "last_attempt_at": timezone.now(),
                    },
                )
                # TaskProgress
                task_progress, _ = TaskProgress.objects.get_or_create(
                    task=task,
                    student=student,
                    defaults={
                        "homework_progress": homework_progress,
                        "total_tests": test_results.total_tests,
                        "best_passed_tests": test_results.passed_tests,
                        "last_attempt_at": timezone.now(),
                        "last_submission": submission,
                    },
                )
                # Update TaskProgress if improved
                updated = False
                if test_results.passed_tests > task_progress.best_passed_tests:
                    task_progress.best_passed_tests = test_results.passed_tests
                    updated = True
                if test_results.total_tests != task_progress.total_tests:
                    task_progress.total_tests = test_results.total_tests
                    updated = True
                task_progress.last_attempt_at = timezone.now()
                task_progress.last_submission = submission
                # Mark as solved if all tests passed
                if test_results.passed_tests >= test_results.total_tests and test_results.total_tests > 0:
                    if not task_progress.is_solved:
                        task_progress.is_solved = True
                        updated = True
                if updated:
                    task_progress.save()
                else:
                    # Always update last_attempt_at and last_submission
                    task_progress.save(update_fields=["last_attempt_at", "last_submission"])

                # Update HomeworkProgress solved_tasks and last_attempt_at
                solved_count = TaskProgress.objects.filter(
                    homework_progress=homework_progress, is_solved=True
                ).count()
                homework_progress.solved_tasks = solved_count
                homework_progress.last_attempt_at = timezone.now()
                homework_progress.update_completion_status()

                # --- End Progress Tracking ---

                # Return detailed response with test results
                response_data = HomeworkSubmissionSerializer(submission).data
                response_data["test_results"] = {
                    "auto_tested": True,
                    "total_tests": test_results.total_tests,
                    "passed_tests": test_results.passed_tests,
                    "success_rate": test_results.success_rate,
                    "execution_time": test_results.overall_execution_time,
                    "memory_usage": test_results.max_memory_usage,
                    "individual_results": [
                        {
                            "passed": result.passed,
                            "output": result.output,
                            "error": result.error,
                            "execution_time": result.execution_time,
                            "timeout": result.timeout,
                        }
                        for result in test_results.test_results
                    ],
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

            except Exception as e:
                # If automated testing fails, still return the submission
                # but indicate that testing failed
                response_data = HomeworkSubmissionSerializer(submission).data
                response_data["test_results"] = {
                    "auto_tested": False,
                    "error": f"Automated testing failed: {str(e)}",
                    "note": "Submission saved successfully, but automatic testing encountered an error",
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            # No auto-testing requested or no code provided
            response_data = HomeworkSubmissionSerializer(submission).data
            response_data["test_results"] = {
                "auto_tested": False,
                "note": "Automatic testing was not performed",
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Get current student's submissions with optional filtering",
        operation_summary="My Submissions",
        tags=["Submissions"],
        manual_parameters=[
            openapi.Parameter(
                "task",
                openapi.IN_QUERY,
                description="Filter by task ID",
                type=openapi.TYPE_INTEGER,
                required=False,
            )
        ],
        responses={
            200: openapi.Response(
                description="Student submissions retrieved successfully",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "task_title": "Calculate Sum",
                            "homework_title": "Python Basics",
                            "is_successful": True,
                            "passed_tests": 5,
                            "total_tests": 5,
                            "submitted_at": "2023-09-05T10:30:00Z",
                        }
                    ]
                },
            )
        },
    )
    @action(detail=False, methods=["get"])
    def my_submissions(self, request):
        """Get current student's submissions."""
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Only students can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN,
            )

        submissions = self.get_queryset().filter(student=request.user.student_profile)

        # Optional filtering
        task_id = request.query_params.get("task")
        if task_id:
            submissions = submissions.filter(task_id=task_id)

        serializer = HomeworkSubmissionListSerializer(submissions, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get submission statistics for teachers with optional filtering",
        operation_summary="Submission Statistics",
        tags=["Submissions"],
        manual_parameters=[
            openapi.Parameter(
                "lesson",
                openapi.IN_QUERY,
                description="Filter by lesson ID",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "homework",
                openapi.IN_QUERY,
                description="Filter by homework ID",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Submission statistics retrieved successfully",
                examples={
                    "application/json": {
                        "total_submissions": 150,
                        "successful_submissions": 120,
                        "success_rate": 80.0,
                        "average_execution_time": 2.5,
                        "top_performers": [],
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Get submission statistics for teachers."""
        if (
            not hasattr(request.user, "teacher_profile")
            and not request.user.is_superuser
        ):
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
        if (
            not hasattr(request.user, "teacher_profile")
            and not request.user.is_superuser
        ):
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

    @swagger_auto_schema(
        operation_description="Automatically re-test a submission against all test cases",
        operation_summary="Auto Re-test Submission",
        tags=["Submissions"],
        responses={
            200: openapi.Response(
                description="Submission re-tested successfully",
                examples={
                    "application/json": {
                        "submission_id": 1,
                        "total_tests": 5,
                        "passed_tests": 3,
                        "success_rate": 60.0,
                        "previous_score": 2,
                        "updated": True,
                    }
                },
            ),
            403: openapi.Response(
                description="Permission denied",
                examples={
                    "application/json": {
                        "error": "Only teachers can re-test submissions"
                    }
                },
            ),
        },
    )
    @action(detail=True, methods=["post"])
    def auto_test(self, request, pk=None):
        """Automatically re-test a submission using the automated testing system."""
        if (
            not hasattr(request.user, "teacher_profile")
            and not request.user.is_superuser
        ):
            return Response(
                {"error": "Only teachers can re-test submissions"},
                status=status.HTTP_403_FORBIDDEN,
            )

        submission = self.get_object()

        if not submission.code_text:
            return Response(
                {"error": "No code found in this submission"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Store previous results for comparison
            previous_passed = submission.passed_tests
            previous_total = submission.total_tests

            # Run automated tests
            test_runner = AutomatedTestRunner()
            test_results = test_runner.evaluate_and_update_submission(submission)

            # Refresh submission from database
            submission.refresh_from_db()

            return Response(
                {
                    "submission_id": submission.id,
                    "student_name": submission.student.user.get_full_name(),
                    "task_title": submission.task.title,
                    "previous_score": {
                        "passed_tests": previous_passed,
                        "total_tests": previous_total,
                        "success_rate": (
                            (previous_passed / previous_total * 100)
                            if previous_total > 0
                            else 0
                        ),
                    },
                    "new_score": {
                        "passed_tests": test_results.passed_tests,
                        "total_tests": test_results.total_tests,
                        "success_rate": test_results.success_rate,
                    },
                    "execution_details": {
                        "execution_time": test_results.overall_execution_time,
                        "memory_usage": test_results.max_memory_usage,
                    },
                    "updated": True,
                    "test_summary": {
                        "total_test_cases": len(test_results.test_results),
                        "passed_count": sum(
                            1 for r in test_results.test_results if r.passed
                        ),
                        "failed_count": sum(
                            1 for r in test_results.test_results if not r.passed
                        ),
                        "timeout_count": sum(
                            1 for r in test_results.test_results if r.timeout
                        ),
                    },
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Automated testing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def task_analytics(self, request):
        """Get detailed analytics for tasks (teachers only)."""
        if (
            not hasattr(request.user, "teacher_profile")
            and not request.user.is_superuser
        ):
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
        if hasattr(request.user, "teacher_profile") and not request.user.is_superuser:
            if not task.homework.lesson.teachers.filter(
                id=request.user.teacher_profile.id
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

    @swagger_auto_schema(
        operation_description="List test cases with filtering based on user role",
        operation_summary="List Test Cases",
        tags=["Submissions"],
        responses={200: TestCaseListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new test case (teachers/admins only)",
        operation_summary="Create Test Case",
        tags=["Submissions"],
        request_body=TestCaseCreateSerializer,
        responses={201: TestCaseSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve detailed test case information",
        operation_summary="Get Test Case Detail",
        tags=["Submissions"],
        responses={200: TestCaseSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a test case (teachers/admins only)",
        operation_summary="Update Test Case",
        tags=["Submissions"],
        request_body=TestCaseCreateSerializer,
        responses={200: TestCaseSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a test case (teachers/admins only)",
        operation_summary="Partially Update Test Case",
        tags=["Submissions"],
        request_body=TestCaseCreateSerializer,
        responses={200: TestCaseSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a test case (teachers/admins only)",
        operation_summary="Delete Test Case",
        tags=["Submissions"],
        responses={204: "Test case deleted successfully"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Filter test cases based on user role."""
        user = self.request.user

        if user.is_superuser:
            # Admins see all test cases
            return TestCase.objects.all().select_related("task__homework__lesson")

        elif hasattr(user, "teacher_profile"):
            # Teachers see test cases for their assigned lessons
            return TestCase.objects.filter(
                task__homework__lesson__teachers=user.teacher_profile
            ).select_related("task__homework__lesson")

        elif hasattr(user, "student_profile"):
            # Students see only non-hidden test cases for lessons they're enrolled in
            from apps.progress.models import StudentProgress

            enrolled_lessons = StudentProgress.objects.filter(
                student=user.student_profile
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
        elif hasattr(user, "student_profile"):
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
