from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.db.models import Count, Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.models import Teacher, Student, Group, Schedule
from .serializers import (
    TeacherGroupSerializer,
    StudentBasicSerializer,
    TeacherGroupDetailSerializer,
    TeacherDashboardSerializer,
    ScheduleSerializer,
    TeacherWeekScheduleSerializer,
    TeacherMultiWeekScheduleSerializer,
)
from .permissions import IsTeacher


class TeacherDashboardView(APIView):
    """
    Teacher Dashboard API

    Provides summary information for teacher dashboard including:
    - Teacher's basic information
    - Total number of groups and students
    - List of groups they teach
    - Recent students
    """

    permission_classes = [IsTeacher]

    @swagger_auto_schema(
        operation_description="Get teacher dashboard summary data",
        operation_summary="Teacher Dashboard",
        responses={
            200: openapi.Response(
                description="Dashboard data retrieved successfully",
                examples={
                    "application/json": {
                        "teacher_info": {
                            "id": 1,
                            "first_name": "John",
                            "last_name": "Doe",
                            "full_name": "John Doe",
                            "phone_number": "+1234567890",
                        },
                        "total_groups": 3,
                        "total_students": 25,
                        "groups": [
                            {
                                "id": 1,
                                "name": "Python Beginners",
                                "created_date": "2024-01-15T10:00:00Z",
                                "student_count": 10,
                                "teacher_count": 2,
                            }
                        ],
                        "recent_students": [
                            {
                                "id": 1,
                                "first_name": "Alice",
                                "last_name": "Smith",
                                "full_name": "Alice Smith",
                                "user_username": "alice_s",
                                "user_email": "alice@example.com",
                            }
                        ],
                    }
                },
            ),
            403: openapi.Response(
                description="Permission denied - Teacher access required"
            ),
        },
        tags=["Teacher Dashboard"],
    )
    def get(self, request):
        try:
            teacher = request.user.teacher_profile

            # Get teacher's groups with annotations
            teacher_groups = teacher.groups.all().annotate(
                annotated_student_count=Count("students"),
                annotated_teacher_count=Count("teachers"),
            )

            # Get all students from teacher's groups
            all_students = (
                Student.objects.filter(groups__in=teacher_groups)
                .distinct()
                .select_related("user")
            )

            # Serialize the groups data properly
            groups_data = TeacherGroupSerializer(teacher_groups, many=True).data

            # Serialize the recent students data
            recent_students_data = StudentBasicSerializer(
                all_students.order_by("-created_at")[:5], many=True
            ).data

            # Prepare dashboard data
            dashboard_data = {
                "teacher_info": {
                    "id": teacher.id,
                    "first_name": teacher.first_name,
                    "last_name": teacher.last_name,
                    "full_name": teacher.full_name,
                    "phone_number": teacher.phone_number,
                },
                "total_groups": teacher_groups.count(),
                "total_students": all_students.count(),
                "groups": groups_data,
                "recent_students": recent_students_data,
            }

            # Return the data directly without re-serializing
            return Response(dashboard_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to load dashboard: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _calculate_week_start(self, request):
        """Calculate week start date based on request parameters"""
        from django.utils import timezone
        from datetime import datetime, timedelta

        # Parse week_start parameter
        week_start_str = request.query_params.get("week_start")
        if week_start_str:
            try:
                return datetime.strptime(week_start_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Start with current week
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())

        # Handle next_week parameter
        next_week = request.query_params.get("next_week", "false").lower() == "true"
        if next_week:
            week_start += timedelta(weeks=1)

        # Handle week_offset parameter
        try:
            week_offset = int(request.query_params.get("week_offset", 0))
            week_start += timedelta(weeks=week_offset)
        except ValueError:
            return Response(
                {"error": "Invalid week_offset. Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return week_start

    def _get_multi_week_schedule(self, teacher, request):
        """Get multiple weeks schedule for a teacher"""
        from datetime import timedelta

        week_start = self._calculate_week_start(request)
        if isinstance(week_start, Response):  # Error response
            return week_start

        # Parse weeks parameter
        try:
            weeks_count = int(request.query_params.get("weeks", 2))
            if weeks_count < 1 or weeks_count > 4:
                return Response(
                    {"error": "Number of weeks must be between 1 and 4"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"error": "Invalid weeks parameter. Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate schedule for multiple weeks
        multi_week_schedule = {}
        total_lessons = 0

        for week_num in range(weeks_count):
            current_week_start = week_start + timedelta(weeks=week_num)
            week_schedule = teacher.get_week_schedule(current_week_start)
            week_end = current_week_start + timedelta(days=6)

            # Format week key as "Week 1 (Sep 22 - Sep 28)"
            week_key = f"Week {week_num + 1} ({current_week_start.strftime('%b %d')} - {week_end.strftime('%b %d')})"

            multi_week_schedule[week_key] = {
                "week_start": current_week_start,
                "week_end": week_end,
                "schedule": week_schedule,
            }

            # Count lessons for this week
            week_lessons = sum(len(lessons) for lessons in week_schedule.values())
            total_lessons += week_lessons

        response_data = {
            "view_type": "multi_week",
            "weeks_count": weeks_count,
            "start_date": week_start,
            "end_date": week_start + timedelta(weeks=weeks_count, days=-1),
            "schedule": multi_week_schedule,
            "total_lessons": total_lessons,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class TeacherGroupsView(ListAPIView):
    """
    Teacher Groups API

    Lists all groups that the authenticated teacher teaches.
    """

    permission_classes = [IsTeacher]
    serializer_class = TeacherGroupSerializer

    def get_queryset(self):
        teacher = self.request.user.teacher_profile
        return (
            teacher.groups.all()
            .annotate(
                annotated_student_count=Count("students"),
                annotated_teacher_count=Count("teachers"),
            )
            .order_by("name")
        )

    @swagger_auto_schema(
        operation_description="Get list of groups that the teacher teaches",
        operation_summary="Teacher's Groups",
        responses={
            200: openapi.Response(
                description="Groups retrieved successfully",
                schema=TeacherGroupSerializer(many=True),
            ),
            403: openapi.Response(
                description="Permission denied - Teacher access required"
            ),
        },
        tags=["Teacher Management"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TeacherGroupDetailView(APIView):
    """
    Teacher Group Detail API

    Provides detailed information about a specific group including all students.
    Only accessible if the teacher teaches this group.
    """

    permission_classes = [IsTeacher]

    @swagger_auto_schema(
        operation_description="Get detailed information about a specific group including students",
        operation_summary="Group Detail for Teacher",
        responses={
            200: openapi.Response(
                description="Group details retrieved successfully",
                schema=TeacherGroupDetailSerializer(),
            ),
            403: openapi.Response(
                description="Permission denied - Teacher access required"
            ),
            404: openapi.Response(
                description="Group not found or teacher doesn't teach this group"
            ),
        },
        tags=["Teacher Management"],
    )
    def get(self, request, group_id):
        try:
            teacher = request.user.teacher_profile

            # Check if teacher teaches this group
            group = (
                teacher.groups.filter(id=group_id)
                .prefetch_related("students__user")
                .first()
            )

            if not group:
                return Response(
                    {"error": "Group not found or you do not teach this group"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = TeacherGroupDetailSerializer(group)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to load group details: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TeacherStudentsView(APIView):
    """
    Teacher Students API

    Lists all students from groups that the authenticated teacher teaches.
    Supports filtering by group.
    """

    permission_classes = [IsTeacher]

    @swagger_auto_schema(
        operation_description="Get list of all students from teacher's groups",
        operation_summary="Teacher's Students",
        manual_parameters=[
            openapi.Parameter(
                "group_id",
                openapi.IN_QUERY,
                description="Filter students by specific group ID",
                type=openapi.TYPE_INTEGER,
                required=False,
            )
        ],
        responses={
            200: openapi.Response(
                description="Students retrieved successfully",
                schema=StudentBasicSerializer(many=True),
            ),
            403: openapi.Response(
                description="Permission denied - Teacher access required"
            ),
        },
        tags=["Teacher Management"],
    )
    def get(self, request):
        try:
            teacher = request.user.teacher_profile
            group_id = request.query_params.get("group_id")

            # Base queryset: students from teacher's groups
            queryset = (
                Student.objects.filter(groups__teachers=teacher)
                .distinct()
                .select_related("user")
            )

            # Filter by specific group if requested
            if group_id:
                queryset = queryset.filter(groups__id=group_id)

            # Order by last name, first name
            students = queryset.order_by("last_name", "first_name")

            serializer = StudentBasicSerializer(students, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to load students: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TeacherScheduleView(APIView):
    """
    Teacher Schedule API

    Provides schedule information for the authenticated teacher:
    - Weekly schedule view with 3 lessons per week
    - Current active schedules with remaining weeks
    - Course and lesson information for each schedule slot
    """

    permission_classes = [IsTeacher]

    @swagger_auto_schema(
        operation_description="Get teacher's weekly schedule",
        operation_summary="Teacher Weekly Schedule",
        manual_parameters=[
            openapi.Parameter(
                "week_start",
                openapi.IN_QUERY,
                description="Start date of the week (YYYY-MM-DD format). Defaults to current week.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False,
            ),
            openapi.Parameter(
                "view_type",
                openapi.IN_QUERY,
                description="Type of schedule view: 'week' for weekly view, 'multi_week' for multiple weeks, 'all' for all schedules",
                type=openapi.TYPE_STRING,
                enum=["week", "multi_week", "all"],
                default="week",
                required=False,
            ),
            openapi.Parameter(
                "next_week",
                openapi.IN_QUERY,
                description="Set to true to get next week's schedule instead of current week",
                type=openapi.TYPE_BOOLEAN,
                default=False,
                required=False,
            ),
            openapi.Parameter(
                "week_offset",
                openapi.IN_QUERY,
                description="Number of weeks to offset from current week (can be negative for past weeks)",
                type=openapi.TYPE_INTEGER,
                default=0,
                required=False,
            ),
            openapi.Parameter(
                "weeks",
                openapi.IN_QUERY,
                description="Number of consecutive weeks to show (1-4). Only works with multi_week view_type.",
                type=openapi.TYPE_INTEGER,
                default=2,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Schedule data retrieved successfully",
                examples={
                    "application/json": {
                        "view_type": "week",
                        "week_start": "2025-09-22",
                        "week_end": "2025-09-28",
                        "schedule": {
                            "Monday": [
                                {
                                    "group": "Python Beginners",
                                    "start_time": "10:00:00",
                                    "end_time": "12:00:00",
                                    "course": "Introduction to Python",
                                    "lesson": "Variables and Data Types",
                                }
                            ],
                            "Wednesday": [
                                {
                                    "group": "Python Intermediate",
                                    "start_time": "14:00:00",
                                    "end_time": "16:00:00",
                                    "course": "Advanced Python",
                                    "lesson": "Object-Oriented Programming",
                                }
                            ],
                            "Friday": [
                                {
                                    "group": "Python Advanced",
                                    "start_time": "16:00:00",
                                    "end_time": "18:00:00",
                                    "course": "Python Projects",
                                    "lesson": "Web Development Basics",
                                }
                            ],
                        },
                        "total_lessons": 3,
                        "navigation": {
                            "current_week": "/api/teacher-mgmt/schedule/",
                            "next_week": "/api/teacher-mgmt/schedule/?next_week=true",
                            "two_weeks": "/api/teacher-mgmt/schedule/?view_type=multi_week&weeks=2",
                        },
                    }
                },
            ),
            400: openapi.Response(description="Invalid request parameters"),
            404: openapi.Response(description="Teacher not found"),
        },
    )
    def get(self, request):
        """Get teacher's schedule based on view type and week"""
        try:
            # Get teacher profile
            teacher = request.user.teacher_profile
        except AttributeError:
            return Response(
                {"error": "Teacher profile not found for authenticated user"},
                status=status.HTTP_404_NOT_FOUND,
            )

        view_type = request.query_params.get("view_type", "week")

        if view_type == "week":
            return self._get_weekly_schedule(teacher, request)
        elif view_type == "multi_week":
            return self._get_multi_week_schedule(teacher, request)
        elif view_type == "all":
            return self._get_all_schedules(teacher)
        else:
            return Response(
                {"error": "Invalid view_type. Use 'week', 'multi_week', or 'all'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _get_weekly_schedule(self, teacher, request):
        """Get weekly schedule for a teacher"""
        from django.utils import timezone
        from datetime import datetime, timedelta

        week_start = self._calculate_week_start(request)
        if isinstance(week_start, Response):  # Error response
            return week_start

        # Get weekly schedule using the teacher method
        schedule = teacher.get_week_schedule(week_start)
        week_end = week_start + timedelta(days=6)

        # Count total lessons for the week
        total_lessons = sum(len(lessons) for lessons in schedule.values())

        response_data = {
            "view_type": "week",
            "week_start": week_start,
            "week_end": week_end,
            "schedule": schedule,
            "total_lessons": total_lessons,
        }

        serializer = TeacherWeekScheduleSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_all_schedules(self, teacher):
        """Get all active schedules for a teacher"""
        schedules = Schedule.objects.filter(
            teacher=teacher, is_active=True
        ).select_related("group", "group__current_course", "group__current_lesson")

        serializer = ScheduleSerializer(schedules, many=True)
        return Response(
            {
                "view_type": "all",
                "schedules": serializer.data,
                "total_schedules": len(serializer.data),
            },
            status=status.HTTP_200_OK,
        )
