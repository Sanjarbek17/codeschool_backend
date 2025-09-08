from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import sys
import io
import multiprocessing

from .services import SecureCodeExecutor, AutomatedTestRunner

# Create your views here.


def execute_code(code):
    """Legacy function for backward compatibility."""
    # Redirect stdout to capture print statements
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    try:
        exec(code, {})
        return new_stdout.getvalue()
    except Exception as e:
        return str(e)
    finally:
        sys.stdout = old_stdout


class ExecuteCodeView(APIView):
    """
    Enhanced code execution view with security features.
    Supports both direct code execution and test case validation.
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Execute Python code securely and return the output",
        operation_summary="Execute Code",
        tags=["Code Editor"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Python code to execute"
                ),
                "timeout": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Execution timeout in seconds (default: 30)",
                    default=30,
                ),
                "input_data": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Optional input data for the code",
                    default="",
                ),
            },
            required=["code"],
        ),
        responses={
            200: openapi.Response(
                description="Code executed successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "output": "Hello World!",
                        "error": "",
                        "execution_time": 0.001,
                        "memory_usage": 1024,
                    }
                },
            ),
            400: openapi.Response(
                description="No code provided or security violation",
                examples={"application/json": {"error": "No code provided"}},
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        code = request.data.get("code", "")
        if not code:
            return Response(
                {"error": "No code provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        timeout = request.data.get("timeout", 30)
        input_data = request.data.get("input_data", "")

        # Use the new secure executor
        executor = SecureCodeExecutor(timeout_seconds=timeout)
        result = executor.execute_code(code, input_data)

        return Response(
            {
                "success": result.passed,
                "output": result.output,
                "error": result.error,
                "execution_time": result.execution_time,
                "memory_usage": result.memory_usage,
                "timeout": result.timeout,
            },
            status=status.HTTP_200_OK,
        )


class TestCodeView(APIView):
    """
    Test student code against specific test cases for a task.
    This is used for immediate feedback during development.
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Test code against visible test cases for a task",
        operation_summary="Test Code Against Task",
        tags=["Code Editor"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Python code to test"
                ),
                "task_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Task ID to test against"
                ),
            },
            required=["code", "task_id"],
        ),
        responses={
            200: openapi.Response(
                description="Code tested successfully",
                examples={
                    "application/json": {
                        "total_tests": 5,
                        "passed_tests": 3,
                        "success_rate": 60.0,
                        "test_results": [
                            {
                                "passed": True,
                                "output": "Expected output",
                                "error": "",
                                "execution_time": 0.001,
                            }
                        ],
                    }
                },
            ),
            400: openapi.Response(
                description="Invalid request",
                examples={"application/json": {"error": "Task not found"}},
            ),
            403: openapi.Response(
                description="Permission denied",
                examples={"application/json": {"error": "Not enrolled in this lesson"}},
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        code = request.data.get("code", "")
        task_id = request.data.get("task_id")

        if not code:
            return Response(
                {"error": "No code provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not task_id:
            return Response(
                {"error": "Task ID required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get the task and check permissions
        from apps.assignments.models import Task
        from apps.submissions.models import TestCase

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is a student and has access to this task
        if hasattr(request.user, "student_profile"):
            from apps.progress.models import StudentProgress

            # Check if student is enrolled in the lesson
            if not StudentProgress.objects.filter(
                student=request.user.student_profile, lesson=task.homework.lesson
            ).exists():
                return Response(
                    {"error": "You are not enrolled in this lesson"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Students can only see non-hidden test cases
            test_cases = TestCase.objects.filter(task=task, hidden=False)
        else:
            # Teachers and admins can see all test cases
            test_cases = TestCase.objects.filter(task=task)

        if not test_cases.exists():
            return Response(
                {
                    "total_tests": 0,
                    "passed_tests": 0,
                    "success_rate": 0.0,
                    "test_results": [],
                    "message": "No test cases available for this task",
                }
            )

        # Run the tests
        test_runner = AutomatedTestRunner()

        test_results = []
        passed_count = 0

        for test_case in test_cases:
            result = test_runner._run_single_test(code, test_case)
            test_results.append(
                {
                    "test_id": test_case.id,
                    "passed": result.passed,
                    "output": result.output,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "memory_usage": result.memory_usage,
                    "timeout": result.timeout,
                    "hidden": test_case.hidden,
                }
            )

            if result.passed:
                passed_count += 1

        total_tests = len(test_results)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0

        return Response(
            {
                "task_title": task.title,
                "total_tests": total_tests,
                "passed_tests": passed_count,
                "success_rate": success_rate,
                "test_results": test_results,
            }
        )
