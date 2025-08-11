from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from .models import Homework, Task
from apps.accounts.permissions import IsAssignedTeacherOrAdmin
from .serializers import (
    HomeworkSerializer,
    HomeworkListSerializer,
    HomeworkCreateUpdateSerializer,
    HomeworkDetailSerializer,
    TaskSerializer,
    TaskListSerializer,
    TaskCreateUpdateSerializer
)


class HomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing homework assignments.
    Provides CRUD operations with different serializers for different actions.
    """
    queryset = Homework.objects.all().select_related('lesson').prefetch_related(
        'lesson__teachers', 'tasks'
    )
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'lesson__title']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return HomeworkListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return HomeworkCreateUpdateSerializer
        elif self.action == 'retrieve':
            return HomeworkDetailSerializer
        return HomeworkSerializer

    def get_permissions(self):
        """
        Set permissions based on action.
        Teachers can create/update/delete homework for assigned lessons.
        Students can only view homework.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAssignedTeacherOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user type and query parameters."""
        queryset = self.queryset
        
        # Filter by lesson if specified
        lesson_id = self.request.query_params.get('lesson', None)
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        
        # For teachers, show only homework from assigned lessons
        if hasattr(self.request.user, 'teacher_profile') and not (
            self.request.user.is_staff or self.request.user.is_superuser
        ):
            queryset = queryset.filter(lesson__teachers=self.request.user.teacher_profile)
        
        return queryset

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """
        Get all tasks for a specific homework assignment.
        """
        homework = self.get_object()
        tasks = homework.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        
        return Response({
            'homework': homework.title,
            'lesson': homework.lesson.title,
            'task_count': tasks.count(),
            'tasks': serializer.data
        })

    @action(detail=True, methods=['post'])
    def add_task(self, request, pk=None):
        """
        Add a new task to this homework assignment.
        Only teachers assigned to the lesson can perform this action.
        """
        homework = self.get_object()
        
        # Prepare data with homework ID
        task_data = request.data.copy()
        task_data['homework'] = homework.id
        
        serializer = TaskCreateUpdateSerializer(data=task_data)
        if serializer.is_valid():
            task = serializer.save()
            
            return Response({
                'message': f'Task "{task.title}" added to homework "{homework.title}"',
                'task': TaskSerializer(task).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get progress statistics for this homework assignment.
        """
        homework = self.get_object()
        
        # Import here to avoid circular imports
        from apps.progress.models import HomeworkProgress
        
        progress_records = HomeworkProgress.objects.filter(homework=homework)
        total_students = progress_records.count()
        completed_students = progress_records.filter(is_completed=True).count()
        
        # Get detailed progress data
        progress_data = [
            {
                'student_name': progress.student.full_name,
                'student_username': progress.student.user.username,
                'solved_tasks': progress.solved_tasks,
                'total_tasks': progress.total_tasks,
                'completion_percentage': progress.completion_percentage,
                'is_completed': progress.is_completed,
                'last_attempt_at': progress.last_attempt_at
            }
            for progress in progress_records.select_related('student__user')
        ]
        
        return Response({
            'homework': homework.title,
            'lesson': homework.lesson.title,
            'total_students': total_students,
            'completed_students': completed_students,
            'completion_rate': round((completed_students / total_students * 100), 1) if total_students > 0 else 0,
            'student_progress': progress_data
        })

    @action(detail=False, methods=['get'])
    def my_homework(self, request):
        """
        Get homework assignments for the current teacher's lessons.
        Only available for teacher users.
        """
        if not hasattr(request.user, 'teacher_profile'):
            return Response(
                {'error': 'Only teachers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        homework = self.get_queryset()
        serializer = HomeworkListSerializer(homework, many=True)
        
        return Response({
            'teacher': request.user.teacher_profile.full_name,
            'homework_count': homework.count(),
            'homework': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get overall homework statistics for the current teacher.
        """
        if not hasattr(request.user, 'teacher_profile'):
            return Response(
                {'error': 'Only teachers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        homework_queryset = self.get_queryset()
        
        # Calculate statistics
        total_homework = homework_queryset.count()
        total_tasks = Task.objects.filter(homework__in=homework_queryset).count()
        
        # Average completion rate
        completion_rates = [hw.get_completion_rate() for hw in homework_queryset]
        avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        return Response({
            'teacher': request.user.teacher_profile.full_name,
            'total_homework': total_homework,
            'total_tasks': total_tasks,
            'average_completion_rate': round(avg_completion_rate, 1),
            'homework_completion_rates': [
                {
                    'homework_title': hw.title,
                    'lesson_title': hw.lesson.title,
                    'completion_rate': round(hw.get_completion_rate(), 1)
                }
                for hw in homework_queryset
            ]
        })


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing individual tasks within homework assignments.
    """
    queryset = Task.objects.all().select_related('homework__lesson').prefetch_related(
        'homework__lesson__teachers'
    )
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'homework__title']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['homework', '-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskSerializer

    def get_permissions(self):
        """
        Set permissions based on action.
        Teachers can create/update/delete tasks for assigned lessons.
        Students can only view tasks.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAssignedTeacherOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user type and query parameters."""
        queryset = self.queryset
        
        # Filter by homework if specified
        homework_id = self.request.query_params.get('homework', None)
        if homework_id:
            queryset = queryset.filter(homework_id=homework_id)
        
        # For teachers, show only tasks from assigned lessons
        if hasattr(self.request.user, 'teacher_profile') and not (
            self.request.user.is_staff or self.request.user.is_superuser
        ):
            queryset = queryset.filter(homework__lesson__teachers=self.request.user.teacher_profile)
        
        return queryset

    @action(detail=True, methods=['get'])
    def test_cases(self, request, pk=None):
        """
        Get test cases for this task.
        """
        task = self.get_object()
        
        # Import here to avoid circular imports
        from apps.submissions.models import TestCase
        
        test_cases = TestCase.objects.filter(task=task)
        
        # Only show visible test cases to students
        if hasattr(request.user, 'student_profile'):
            test_cases = test_cases.filter(hidden=False)
        
        test_case_data = [
            {
                'id': tc.id,
                'hidden': tc.hidden,
                'input_data': tc.input_data if not tc.hidden or hasattr(request.user, 'teacher_profile') else 'Hidden',
                'expected_output': tc.expected_output if not tc.hidden or hasattr(request.user, 'teacher_profile') else 'Hidden',
                'timeout_seconds': tc.timeout_seconds,
                'created_at': tc.created_at
            }
            for tc in test_cases
        ]
        
        return Response({
            'task': task.title,
            'homework': task.homework.title,
            'test_case_count': test_cases.count(),
            'test_cases': test_case_data
        })

    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """
        Get submissions for this task.
        Teachers see all submissions, students see only their own.
        """
        task = self.get_object()
        
        # Import here to avoid circular imports
        from apps.submissions.models import HomeworkSubmission
        
        submissions = HomeworkSubmission.objects.filter(task=task)
        
        # Students can only see their own submissions
        if hasattr(request.user, 'student_profile'):
            submissions = submissions.filter(student=request.user.student_profile)
        
        submission_data = [
            {
                'id': submission.id,
                'student_name': submission.student.full_name,
                'student_username': submission.student.user.username,
                'passed_tests': submission.passed_tests,
                'total_tests': submission.total_tests,
                'success_rate': submission.success_rate,
                'is_successful': submission.is_successful,
                'submitted_at': submission.submitted_at,
                'execution_time': submission.execution_time,
                'memory_usage': submission.memory_usage
            }
            for submission in submissions.select_related('student__user')
        ]
        
        return Response({
            'task': task.title,
            'homework': task.homework.title,
            'submission_count': submissions.count(),
            'submissions': submission_data
        })
