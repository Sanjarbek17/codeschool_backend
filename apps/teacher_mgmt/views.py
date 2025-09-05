from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.db.models import Count, Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.models import Teacher, Student, Group
from .serializers import (
    TeacherGroupSerializer,
    StudentBasicSerializer,
    TeacherGroupDetailSerializer,
    TeacherDashboardSerializer,
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

            # Get teacher's groups
            teacher_groups = teacher.groups.all().annotate(
                student_count=Count("students"), teacher_count=Count("teachers")
            )

            # Get all students from teacher's groups
            all_students = (
                Student.objects.filter(groups__in=teacher_groups)
                .distinct()
                .select_related("user")
            )

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
                "groups": TeacherGroupSerializer(teacher_groups, many=True).data,
                "recent_students": StudentBasicSerializer(
                    all_students.order_by("-created_at")[:5], many=True
                ).data,
            }

            return Response(dashboard_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to load dashboard: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TeacherGroupsView(ListAPIView):
    """
    Teacher Groups API

    Lists all groups that the authenticated teacher teaches.
    """

    permission_classes = [IsTeacher]
    serializer_class = TeacherGroupSerializer

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
    def get_queryset(self):
        teacher = self.request.user.teacher_profile
        return (
            teacher.groups.all()
            .annotate(student_count=Count("students"), teacher_count=Count("teachers"))
            .order_by("name")
        )


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
