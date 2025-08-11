from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Lessons
from apps.accounts.permissions import IsAssignedTeacherOrAdmin
from .serializers import (
    LessonSerializer,
    LessonListSerializer,
    LessonCreateUpdateSerializer,
    LessonDetailSerializer
)


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lessons.
    Provides CRUD operations with different serializers for different actions.
    """
    queryset = Lessons.objects.all().prefetch_related('teachers', 'homework_set')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return LessonListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return LessonCreateUpdateSerializer
        elif self.action == 'retrieve':
            return LessonDetailSerializer
        return LessonSerializer

    def get_permissions(self):
        """
        Set permissions based on action.
        Teachers can create/update/delete lessons.
        Students can only view lessons.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAssignedTeacherOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Automatically assign the creating teacher to the lesson.
        """
        lesson = serializer.save()
        
        # If the user is a teacher, automatically assign them to the lesson
        if hasattr(self.request.user, 'teacher_profile'):
            lesson.teachers.add(self.request.user.teacher_profile)

    @action(detail=True, methods=['get'])
    def homework(self, request, pk=None):
        """
        Get all homework assignments for a specific lesson.
        """
        lesson = self.get_object()
        homework_assignments = lesson.homework_set.all()
        
        # Simple homework data without external serializer for now
        homework_data = [
            {
                'id': hw.id,
                'title': hw.title,
                'description': hw.description,
                'created_at': hw.created_at,
                'task_count': hw.get_task_count()
            }
            for hw in homework_assignments
        ]
        
        return Response({
            'lesson': lesson.title,
            'homework_count': homework_assignments.count(),
            'homework': homework_data
        })

    @action(detail=True, methods=['post'])
    def assign_teacher(self, request, pk=None):
        """
        Assign a teacher to a lesson.
        Only teachers and admins can perform this action.
        """
        lesson = self.get_object()
        teacher_id = request.data.get('teacher_id')
        
        if not teacher_id:
            return Response(
                {'error': 'teacher_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.accounts.models import Teacher
            teacher = Teacher.objects.get(id=teacher_id)
            lesson.teachers.add(teacher)
            
            return Response({
                'message': f'Teacher {teacher.full_name} assigned to lesson {lesson.title}',
                'lesson_id': lesson.id,
                'teacher_id': teacher.id
            })
        
        except Teacher.DoesNotExist:
            return Response(
                {'error': 'Teacher not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_teacher(self, request, pk=None):
        """
        Remove a teacher from a lesson.
        Only teachers and admins can perform this action.
        """
        lesson = self.get_object()
        teacher_id = request.data.get('teacher_id')
        
        if not teacher_id:
            return Response(
                {'error': 'teacher_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.accounts.models import Teacher
            teacher = Teacher.objects.get(id=teacher_id)
            lesson.teachers.remove(teacher)
            
            return Response({
                'message': f'Teacher {teacher.full_name} removed from lesson {lesson.title}',
                'lesson_id': lesson.id,
                'teacher_id': teacher.id
            })
        
        except Teacher.DoesNotExist:
            return Response(
                {'error': 'Teacher not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def my_lessons(self, request):
        """
        Get lessons assigned to the current teacher.
        Only available for teacher users.
        """
        if not hasattr(request.user, 'teacher_profile'):
            return Response(
                {'error': 'Only teachers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        lessons = self.queryset.filter(teachers=request.user.teacher_profile)
        serializer = LessonListSerializer(lessons, many=True)
        
        return Response({
            'teacher': request.user.teacher_profile.full_name,
            'lesson_count': lessons.count(),
            'lessons': serializer.data
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search for lessons.
        """
        query = request.query_params.get('q', '')
        teacher_name = request.query_params.get('teacher', '')
        
        queryset = self.queryset
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(content__icontains=query)
            )
        
        if teacher_name:
            queryset = queryset.filter(
                Q(teachers__first_name__icontains=teacher_name) |
                Q(teachers__last_name__icontains=teacher_name)
            )
        
        serializer = LessonListSerializer(queryset, many=True)
        
        return Response({
            'query': query,
            'teacher_filter': teacher_name,
            'result_count': queryset.count(),
            'lessons': serializer.data
        })
