from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Lessons, Attendance
from apps.accounts.permissions import IsAssignedTeacherOrAdmin
from .serializers import (
    LessonSerializer,
    LessonListSerializer,
    LessonCreateUpdateSerializer,
    LessonDetailSerializer,
    AttendanceSerializer,
    AttendanceListSerializer,
    AttendanceCreateUpdateSerializer,
)


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lessons.
    Provides CRUD operations with different serializers for different actions.
    """

    queryset = Lessons.objects.all().prefetch_related("teachers", "homework_set")
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "content"]
    ordering_fields = ["created_at", "updated_at", "title"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return LessonListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return LessonCreateUpdateSerializer
        elif self.action == "retrieve":
            return LessonDetailSerializer
        return LessonSerializer

    def get_permissions(self):
        """
        Set permissions based on action.
        Teachers can create/update/delete lessons.
        Students can only view lessons.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsAssignedTeacherOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_description="List all lessons with optional filtering",
        operation_summary="List Lessons",
        tags=["Courses"],
        responses={200: LessonListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new lesson",
        operation_summary="Create Lesson",
        tags=["Courses"],
        request_body=LessonCreateUpdateSerializer,
        responses={201: LessonDetailSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve detailed lesson information",
        operation_summary="Get Lesson Detail",
        tags=["Courses"],
        responses={200: LessonDetailSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a lesson",
        operation_summary="Update Lesson",
        tags=["Courses"],
        request_body=LessonCreateUpdateSerializer,
        responses={200: LessonDetailSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a lesson",
        operation_summary="Partially Update Lesson",
        tags=["Courses"],
        request_body=LessonCreateUpdateSerializer,
        responses={200: LessonDetailSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a lesson",
        operation_summary="Delete Lesson",
        tags=["Courses"],
        responses={204: "Lesson deleted successfully"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Automatically assign the creating teacher to the lesson.
        """
        lesson = serializer.save()

        # If the user is a teacher, automatically assign them to the lesson
        if hasattr(self.request.user, "teacher_profile"):
            lesson.teachers.add(self.request.user.teacher_profile)

    @swagger_auto_schema(
        operation_description="Get all homework assignments for a specific lesson",
        operation_summary="Get Lesson Homework",
        tags=["Courses"],
        responses={
            200: openapi.Response(
                description="Lesson homework retrieved successfully",
                examples={
                    "application/json": {
                        "lesson": "Introduction to Python",
                        "homework_count": 3,
                        "homework": [],
                    }
                },
            )
        },
    )
    @action(detail=True, methods=["get"])
    def homework(self, request, pk=None):
        """
        Get all homework assignments for a specific lesson.
        """
        lesson = self.get_object()
        homework_assignments = lesson.homework_set.all()

        # Simple homework data without external serializer for now
        homework_data = [
            {
                "id": hw.id,
                "title": hw.title,
                "description": hw.description,
                "created_at": hw.created_at,
                "task_count": hw.get_task_count(),
            }
            for hw in homework_assignments
        ]

        return Response(
            {
                "lesson": lesson.title,
                "homework_count": homework_assignments.count(),
                "homework": homework_data,
            }
        )

    @swagger_auto_schema(
        operation_description="Assign a teacher to a lesson",
        operation_summary="Assign Teacher to Lesson",
        tags=["Courses"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "teacher_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="ID of the teacher to assign"
                )
            },
            required=["teacher_id"],
        ),
        responses={
            200: openapi.Response(
                description="Teacher assigned successfully",
                examples={
                    "application/json": {
                        "message": "Teacher John Doe assigned to lesson Introduction to Python",
                        "lesson_id": 1,
                        "teacher_id": 1,
                    }
                },
            )
        },
    )
    @action(detail=True, methods=["post"])
    def assign_teacher(self, request, pk=None):
        """
        Assign a teacher to a lesson.
        Only teachers and admins can perform this action.
        """
        lesson = self.get_object()
        teacher_id = request.data.get("teacher_id")

        if not teacher_id:
            return Response(
                {"error": "teacher_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from apps.accounts.models import Teacher

            teacher = Teacher.objects.get(id=teacher_id)
            lesson.teachers.add(teacher)

            return Response(
                {
                    "message": f"Teacher {teacher.full_name} assigned to lesson {lesson.title}",
                    "lesson_id": lesson.id,
                    "teacher_id": teacher.id,
                }
            )

        except Teacher.DoesNotExist:
            return Response(
                {"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Remove a teacher from a lesson",
        operation_summary="Remove Teacher from Lesson",
        tags=["Courses"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "teacher_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="ID of the teacher to remove"
                )
            },
            required=["teacher_id"],
        ),
        responses={
            200: openapi.Response(
                description="Teacher removed successfully",
                examples={
                    "application/json": {
                        "message": "Teacher John Doe removed from lesson Introduction to Python",
                        "lesson_id": 1,
                        "teacher_id": 1,
                    }
                },
            )
        },
    )
    @action(detail=True, methods=["post"])
    def remove_teacher(self, request, pk=None):
        """
        Remove a teacher from a lesson.
        Only teachers and admins can perform this action.
        """
        lesson = self.get_object()
        teacher_id = request.data.get("teacher_id")

        if not teacher_id:
            return Response(
                {"error": "teacher_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from apps.accounts.models import Teacher

            teacher = Teacher.objects.get(id=teacher_id)
            lesson.teachers.remove(teacher)

            return Response(
                {
                    "message": f"Teacher {teacher.full_name} removed from lesson {lesson.title}",
                    "lesson_id": lesson.id,
                    "teacher_id": teacher.id,
                }
            )

        except Teacher.DoesNotExist:
            return Response(
                {"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Get lessons assigned to the current teacher",
        operation_summary="Get My Lessons",
        tags=["Courses"],
        responses={
            200: openapi.Response(
                description="Teacher's lessons retrieved successfully",
                examples={
                    "application/json": {
                        "teacher": "John Doe",
                        "lesson_count": 5,
                        "lessons": [],
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["get"])
    def my_lessons(self, request):
        """
        Get lessons assigned to the current teacher.
        Only available for teacher users.
        """
        if not hasattr(request.user, "teacher_profile"):
            return Response(
                {"error": "Only teachers can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN,
            )

        lessons = self.queryset.filter(teachers=request.user.teacher_profile)
        serializer = LessonListSerializer(lessons, many=True)

        return Response(
            {
                "teacher": request.user.teacher_profile.full_name,
                "lesson_count": lessons.count(),
                "lessons": serializer.data,
            }
        )

    @swagger_auto_schema(
        operation_description="Advanced search for lessons with optional filtering",
        operation_summary="Search Lessons",
        tags=["Courses"],
        manual_parameters=[
            openapi.Parameter(
                "q",
                openapi.IN_QUERY,
                description="Search query for title, description, or content",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "teacher",
                openapi.IN_QUERY,
                description="Filter by teacher name",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Search results retrieved successfully",
                examples={
                    "application/json": {
                        "query": "python",
                        "teacher_filter": "john",
                        "result_count": 3,
                        "lessons": [],
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Advanced search for lessons.
        """
        query = request.query_params.get("q", "")
        teacher_name = request.query_params.get("teacher", "")

        queryset = self.queryset

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(content__icontains=query)
            )

        if teacher_name:
            queryset = queryset.filter(
                Q(teachers__first_name__icontains=teacher_name)
                | Q(teachers__last_name__icontains=teacher_name)
            )

        serializer = LessonListSerializer(queryset, many=True)

        return Response(
            {
                "query": query,
                "teacher_filter": teacher_name,
                "result_count": queryset.count(),
                "lessons": serializer.data,
            }
        )


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance records.
    Teachers can create and update attendance for their groups.
    """

    queryset = Attendance.objects.all().select_related(
        "student__user", "lesson", "group", "teacher__user"
    )
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "student__first_name",
        "student__last_name",
        "lesson__title",
        "group__name",
    ]
    ordering_fields = ["date", "created_at", "status"]
    ordering = ["-date", "-created_at"]

    @swagger_auto_schema(
        operation_description="List all attendance records with optional filtering",
        operation_summary="List Attendance",
        tags=["Courses"],
        responses={200: AttendanceListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new attendance record",
        operation_summary="Create Attendance",
        tags=["Courses"],
        request_body=AttendanceCreateUpdateSerializer,
        responses={201: AttendanceSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve detailed attendance record information",
        operation_summary="Get Attendance Detail",
        tags=["Courses"],
        responses={200: AttendanceSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an attendance record",
        operation_summary="Update Attendance",
        tags=["Courses"],
        request_body=AttendanceCreateUpdateSerializer,
        responses={200: AttendanceSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update an attendance record",
        operation_summary="Partially Update Attendance",
        tags=["Courses"],
        request_body=AttendanceCreateUpdateSerializer,
        responses={200: AttendanceSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an attendance record",
        operation_summary="Delete Attendance",
        tags=["Courses"],
        responses={204: "Attendance record deleted successfully"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return AttendanceListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return AttendanceCreateUpdateSerializer
        return AttendanceSerializer

    def get_queryset(self):
        """Filter attendance records based on user role."""
        queryset = super().get_queryset()
        user = self.request.user

        # Teachers can only see attendance for their groups
        if hasattr(user, "teacher_profile"):
            queryset = queryset.filter(group__teachers=user.teacher_profile)
        # Students can only see their own attendance
        elif hasattr(user, "student_profile"):
            queryset = queryset.filter(student=user.student_profile)

        return queryset

    def perform_create(self, serializer):
        """Set the teacher to current user if they are a teacher."""
        if hasattr(self.request.user, "teacher_profile"):
            serializer.save(teacher=self.request.user.teacher_profile)
        else:
            serializer.save()

    @swagger_auto_schema(
        operation_description="Get attendance records filtered by group and optional date",
        operation_summary="Get Attendance by Group",
        tags=["Courses"],
        manual_parameters=[
            openapi.Parameter(
                "group_id",
                openapi.IN_QUERY,
                description="Group ID (required)",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "date",
                openapi.IN_QUERY,
                description="Filter by specific date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Attendance records retrieved successfully",
                examples={
                    "application/json": {
                        "group_id": "1",
                        "date_filter": "2023-09-05",
                        "result_count": 25,
                        "attendance_records": [],
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["GET"])
    def by_group(self, request):
        """Get attendance records filtered by group."""
        group_id = request.query_params.get("group_id")
        date = request.query_params.get("date")

        if not group_id:
            return Response(
                {"error": "group_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(group_id=group_id)

        if date:
            queryset = queryset.filter(date=date)

        serializer = AttendanceListSerializer(queryset, many=True)
        return Response(
            {
                "group_id": group_id,
                "date_filter": date,
                "result_count": queryset.count(),
                "attendance_records": serializer.data,
            }
        )

    @swagger_auto_schema(
        operation_description="Get attendance records for a specific student",
        operation_summary="Get Attendance by Student",
        tags=["Courses"],
        manual_parameters=[
            openapi.Parameter(
                "student_id",
                openapi.IN_QUERY,
                description="Student ID (required)",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Student attendance records retrieved successfully",
                examples={
                    "application/json": {
                        "student_id": "1",
                        "result_count": 10,
                        "attendance_records": [],
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["GET"])
    def by_student(self, request):
        """Get attendance records for a specific student."""
        student_id = request.query_params.get("student_id")

        if not student_id:
            return Response(
                {"error": "student_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(student_id=student_id)
        serializer = AttendanceListSerializer(queryset, many=True)

        return Response(
            {
                "student_id": student_id,
                "result_count": queryset.count(),
                "attendance_records": serializer.data,
            }
        )

    @swagger_auto_schema(
        operation_description="Create multiple attendance records at once",
        operation_summary="Bulk Create Attendance",
        tags=["Courses"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "attendance_records": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    description="Array of attendance records to create",
                )
            },
            required=["attendance_records"],
        ),
        responses={
            201: openapi.Response(
                description="Attendance records created successfully",
                examples={
                    "application/json": {
                        "message": "25 attendance records created successfully"
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["POST"])
    def bulk_create(self, request):
        """Create multiple attendance records at once."""
        attendance_data = request.data.get("attendance_records", [])

        if not attendance_data:
            return Response(
                {"error": "attendance_records list is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AttendanceCreateUpdateSerializer(data=attendance_data, many=True)

        if serializer.is_valid():
            # Set teacher to current user if they are a teacher
            if hasattr(request.user, "teacher_profile"):
                for attendance in serializer.validated_data:
                    attendance["teacher"] = request.user.teacher_profile

            serializer.save()
            return Response(
                {
                    "message": f"{len(attendance_data)} attendance records created successfully"
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
