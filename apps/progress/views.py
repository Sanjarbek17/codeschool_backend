from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Max, Min, Q, F
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from .models import HomeworkProgress, TaskProgress
from .serializers import (
    HomeworkProgressSerializer, HomeworkProgressListSerializer,
    HomeworkProgressCreateUpdateSerializer, TaskProgressSerializer,
    TaskProgressListSerializer, TaskProgressCreateUpdateSerializer,
    StudentProgressSummarySerializer, TeacherProgressDashboardSerializer,
    LessonProgressAnalyticsSerializer, HomeworkAnalyticsSerializer,
    StudentAnalyticsSerializer, ProgressComparisonSerializer,
    LearningPathSerializer, ProgressInsightsSerializer
)
from apps.accounts.permissions import (
    IsTeacherOrAdmin, IsStudentOwnerOrTeacherOrAdmin,
    IsAssignedTeacherOrAdmin, IsStudentOrAdmin
)

User = get_user_model()


class HomeworkProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing homework progress tracking.
    
    - Students can view their own progress
    - Teachers can view progress for their assigned lessons
    - Admins have full access
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter homework progress based on user role."""
        user = self.request.user
        
        if user.is_superuser:
            # Admins see all homework progress
            return HomeworkProgress.objects.all().select_related(
                'student__user', 'homework__lesson'
            ).prefetch_related('homework__lesson__teachers')
        
        elif hasattr(user, 'teacher'):
            # Teachers see progress for their assigned lessons
            return HomeworkProgress.objects.filter(
                homework__lesson__teachers=user.teacher
            ).select_related(
                'student__user', 'homework__lesson'
            ).prefetch_related('homework__lesson__teachers')
        
        elif hasattr(user, 'student'):
            # Students see only their own progress
            return HomeworkProgress.objects.filter(
                student=user.student
            ).select_related(
                'student__user', 'homework__lesson'
            ).prefetch_related('homework__lesson__teachers')
        
        return HomeworkProgress.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return HomeworkProgressListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return HomeworkProgressCreateUpdateSerializer
        return HomeworkProgressSerializer
    
    def get_permissions(self):
        """Get permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only teachers/admins can modify progress
            permission_classes = [IsTeacherOrAdmin]
        else:
            # View permissions handled in get_queryset
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def my_progress(self, request):
        """Get current student's homework progress."""
        if not hasattr(request.user, 'student'):
            return Response(
                {'error': 'Only students can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        progress = self.get_queryset().filter(student=request.user.student)
        
        # Optional filtering
        lesson_id = request.query_params.get('lesson')
        homework_id = request.query_params.get('homework')
        is_completed = request.query_params.get('completed')
        
        if lesson_id:
            progress = progress.filter(homework__lesson_id=lesson_id)
        if homework_id:
            progress = progress.filter(homework_id=homework_id)
        if is_completed is not None:
            completed = is_completed.lower() == 'true'
            progress = progress.filter(is_completed=completed)
        
        serializer = HomeworkProgressListSerializer(progress, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get student progress summary."""
        if not hasattr(request.user, 'student'):
            return Response(
                {'error': 'Only students can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        student = request.user.student
        progress_queryset = self.get_queryset().filter(student=student)
        
        # Calculate summary statistics
        total_homework = progress_queryset.count()
        completed_homework = progress_queryset.filter(is_completed=True).count()
        homework_completion_rate = (completed_homework / total_homework * 100) if total_homework > 0 else 0
        
        # Task statistics
        task_progress = TaskProgress.objects.filter(student=student)
        total_tasks = task_progress.count()
        completed_tasks = task_progress.filter(is_solved=True).count()
        task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Average task score
        avg_score = task_progress.aggregate(
            avg_score=Avg('best_passed_tests', output_field=F('total_tests'))
        )['avg_score'] or 0
        
        # Recent activity
        last_activity = progress_queryset.aggregate(
            last_activity=Max('last_attempt_at')
        )['last_activity']
        
        # Recent homework (last 5)
        recent_homework = progress_queryset.order_by('-last_attempt_at')[:5]
        
        summary_data = {
            'student': {
                'id': student.id,
                'full_name': student.user.get_full_name(),
                'username': student.user.username
            },
            'total_homework': total_homework,
            'completed_homework': completed_homework,
            'homework_completion_rate': homework_completion_rate,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'task_completion_rate': task_completion_rate,
            'average_task_score': avg_score,
            'last_activity': last_activity,
            'recent_homework': HomeworkProgressListSerializer(recent_homework, many=True).data
        }
        
        serializer = StudentProgressSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def teacher_dashboard(self, request):
        """Get teacher progress dashboard."""
        if not hasattr(request.user, 'teacher') and not request.user.is_superuser:
            return Response(
                {'error': 'Only teachers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get teacher's lessons
        if hasattr(request.user, 'teacher'):
            lessons = request.user.teacher.lessons.all()
        else:
            from apps.courses.models import Lessons
            lessons = Lessons.objects.all()
        
        dashboard_data = []
        
        for lesson in lessons:
            # Get progress for this lesson
            lesson_progress = HomeworkProgress.objects.filter(homework__lesson=lesson)
            lesson_tasks = TaskProgress.objects.filter(task__homework__lesson=lesson)
            
            # Calculate metrics
            total_students = lesson_progress.values('student').distinct().count()
            total_homework = lesson_progress.values('homework').distinct().count()
            total_tasks = lesson_tasks.values('task').distinct().count()
            
            # Completion rates
            homework_completion = lesson_progress.filter(is_completed=True).count()
            task_completion = lesson_tasks.filter(is_solved=True).count()
            
            avg_homework_completion = (homework_completion / lesson_progress.count() * 100) if lesson_progress.count() > 0 else 0
            avg_task_completion = (task_completion / lesson_tasks.count() * 100) if lesson_tasks.count() > 0 else 0
            
            # Active students (activity in last 7 days)
            week_ago = timezone.now() - timedelta(days=7)
            active_students = lesson_progress.filter(
                last_attempt_at__gte=week_ago
            ).values('student').distinct().count()
            
            # Recent activity
            recent_activity = lesson_progress.aggregate(
                recent=Max('last_attempt_at')
            )['recent']
            
            dashboard_data.append({
                'lesson_id': lesson.id,
                'lesson_title': lesson.title,
                'total_students': total_students,
                'total_homework': total_homework,
                'total_tasks': total_tasks,
                'average_homework_completion': avg_homework_completion,
                'average_task_completion': avg_task_completion,
                'active_students': active_students,
                'recent_activity': recent_activity
            })
        
        serializer = TeacherProgressDashboardSerializer(dashboard_data, many=True)
        return Response({
            'teacher': request.user.get_full_name(),
            'dashboard': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def lesson_analytics(self, request):
        """Get detailed analytics for a specific lesson."""
        if not hasattr(request.user, 'teacher') and not request.user.is_superuser:
            return Response(
                {'error': 'Only teachers can access analytics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        lesson_id = request.query_params.get('lesson')
        if not lesson_id:
            return Response(
                {'error': 'lesson parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.courses.models import Lessons
        try:
            lesson = Lessons.objects.get(id=lesson_id)
        except Lessons.DoesNotExist:
            return Response(
                {'error': 'Lesson not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check teacher access
        if hasattr(request.user, 'teacher') and not request.user.is_superuser:
            if not lesson.teachers.filter(id=request.user.teacher.id).exists():
                return Response(
                    {'error': 'You do not have access to this lesson'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Get lesson progress data
        lesson_progress = HomeworkProgress.objects.filter(homework__lesson=lesson)
        lesson_tasks = TaskProgress.objects.filter(task__homework__lesson=lesson)
        
        # Overview statistics
        total_students = lesson_progress.values('student').distinct().count()
        total_homework = lesson_progress.values('homework').distinct().count()
        total_tasks = lesson_tasks.values('task').distinct().count()
        
        completed_homework = lesson_progress.filter(is_completed=True).count()
        completed_tasks = lesson_tasks.filter(is_solved=True).count()
        
        # Homework breakdown
        homework_breakdown = lesson_progress.values(
            'homework__title', 'homework__id'
        ).annotate(
            total_students=Count('student', distinct=True),
            completed_students=Count('student', filter=Q(is_completed=True)),
            avg_completion_percentage=Avg('solved_tasks') / Avg('total_tasks') * 100
        )
        
        # Student rankings
        student_rankings = lesson_progress.values(
            'student__user__first_name', 'student__user__last_name'
        ).annotate(
            completed_homework=Count('id', filter=Q(is_completed=True)),
            total_homework=Count('id'),
            completion_rate=Count('id', filter=Q(is_completed=True)) / Count('id') * 100
        ).order_by('-completion_rate')[:10]
        
        analytics_data = {
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description
            },
            'overview': {
                'total_students': total_students,
                'total_homework': total_homework,
                'total_tasks': total_tasks,
                'homework_completion_rate': (completed_homework / lesson_progress.count() * 100) if lesson_progress.count() > 0 else 0,
                'task_completion_rate': (completed_tasks / lesson_tasks.count() * 100) if lesson_tasks.count() > 0 else 0
            },
            'homework_breakdown': list(homework_breakdown),
            'student_rankings': list(student_rankings),
            'difficulty_analysis': [],  # Can be implemented with AI analysis
            'time_trends': []  # Can be implemented with time-series data
        }
        
        serializer = LessonProgressAnalyticsSerializer(analytics_data)
        return Response(serializer.data)


class TaskProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task progress tracking.
    
    - Students can view their own task progress
    - Teachers can view progress for their assigned lessons
    - Admins have full access
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter task progress based on user role."""
        user = self.request.user
        
        if user.is_superuser:
            # Admins see all task progress
            return TaskProgress.objects.all().select_related(
                'student__user', 'task__homework__lesson', 'last_submission'
            ).prefetch_related('task__homework__lesson__teachers')
        
        elif hasattr(user, 'teacher'):
            # Teachers see progress for their assigned lessons
            return TaskProgress.objects.filter(
                task__homework__lesson__teachers=user.teacher
            ).select_related(
                'student__user', 'task__homework__lesson', 'last_submission'
            ).prefetch_related('task__homework__lesson__teachers')
        
        elif hasattr(user, 'student'):
            # Students see only their own progress
            return TaskProgress.objects.filter(
                student=user.student
            ).select_related(
                'student__user', 'task__homework__lesson', 'last_submission'
            ).prefetch_related('task__homework__lesson__teachers')
        
        return TaskProgress.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TaskProgressListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskProgressCreateUpdateSerializer
        return TaskProgressSerializer
    
    def get_permissions(self):
        """Get permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only teachers/admins can modify progress
            permission_classes = [IsTeacherOrAdmin]
        else:
            # View permissions handled in get_queryset
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def my_task_progress(self, request):
        """Get current student's task progress."""
        if not hasattr(request.user, 'student'):
            return Response(
                {'error': 'Only students can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        progress = self.get_queryset().filter(student=request.user.student)
        
        # Optional filtering
        homework_id = request.query_params.get('homework')
        task_id = request.query_params.get('task')
        is_solved = request.query_params.get('solved')
        
        if homework_id:
            progress = progress.filter(task__homework_id=homework_id)
        if task_id:
            progress = progress.filter(task_id=task_id)
        if is_solved is not None:
            solved = is_solved.lower() == 'true'
            progress = progress.filter(is_solved=solved)
        
        serializer = TaskProgressListSerializer(progress, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_from_submission(self, request):
        """Update task progress from a submission (internal API)."""
        if not hasattr(request.user, 'student'):
            return Response(
                {'error': 'Only students can update progress'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        submission_id = request.data.get('submission_id')
        if not submission_id:
            return Response(
                {'error': 'submission_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.submissions.models import HomeworkSubmission
        try:
            submission = HomeworkSubmission.objects.get(
                id=submission_id, student=request.user.student
            )
        except HomeworkSubmission.DoesNotExist:
            return Response(
                {'error': 'Submission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create task progress
        task_progress, created = TaskProgress.objects.get_or_create(
            task=submission.task,
            student=request.user.student,
            defaults={
                'total_tests': submission.total_tests,
                'best_passed_tests': submission.passed_tests,
                'last_attempt_at': submission.submitted_at,
                'last_submission': submission
            }
        )
        
        # Update if this submission is better
        if not created:
            if submission.passed_tests > task_progress.best_passed_tests:
                task_progress.best_passed_tests = submission.passed_tests
            task_progress.last_attempt_at = submission.submitted_at
            task_progress.last_submission = submission
            task_progress.save()
        
        # Update solved status
        task_progress.update_solved_status()
        
        # Update homework progress
        self._update_homework_progress(submission.task.homework, request.user.student)
        
        serializer = TaskProgressSerializer(task_progress)
        return Response(serializer.data)
    
    def _update_homework_progress(self, homework, student):
        """Update homework progress based on task progress."""
        # Get all tasks for this homework
        from apps.assignments.models import Task
        homework_tasks = Task.objects.filter(homework=homework)
        total_tasks = homework_tasks.count()
        
        # Get solved tasks count
        solved_tasks = TaskProgress.objects.filter(
            task__homework=homework,
            student=student,
            is_solved=True
        ).count()
        
        # Get or create homework progress
        homework_progress, created = HomeworkProgress.objects.get_or_create(
            homework=homework,
            student=student,
            defaults={
                'total_tasks': total_tasks,
                'solved_tasks': solved_tasks,
                'last_attempt_at': timezone.now()
            }
        )
        
        # Update homework progress
        if not created:
            homework_progress.total_tasks = total_tasks
            homework_progress.solved_tasks = solved_tasks
            homework_progress.last_attempt_at = timezone.now()
            homework_progress.save()
        
        # Update completion status
        homework_progress.update_completion_status()
    
    @action(detail=False, methods=['get'])
    def homework_analytics(self, request):
        """Get detailed analytics for specific homework."""
        if not hasattr(request.user, 'teacher') and not request.user.is_superuser:
            return Response(
                {'error': 'Only teachers can access analytics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        homework_id = request.query_params.get('homework')
        if not homework_id:
            return Response(
                {'error': 'homework parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.assignments.models import Homework
        try:
            homework = Homework.objects.get(id=homework_id)
        except Homework.DoesNotExist:
            return Response(
                {'error': 'Homework not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check teacher access
        if hasattr(request.user, 'teacher') and not request.user.is_superuser:
            if not homework.lesson.teachers.filter(id=request.user.teacher.id).exists():
                return Response(
                    {'error': 'You do not have access to this homework'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Get homework progress data
        homework_progress = HomeworkProgress.objects.filter(homework=homework)
        task_progress = TaskProgress.objects.filter(task__homework=homework)
        
        # Overview statistics
        total_students = homework_progress.count()
        completed_students = homework_progress.filter(is_completed=True).count()
        
        # Task breakdown
        task_breakdown = task_progress.values(
            'task__title', 'task__id'
        ).annotate(
            total_students=Count('student', distinct=True),
            solved_students=Count('student', filter=Q(is_solved=True)),
            avg_score=Avg('best_passed_tests') / Avg('total_tests') * 100
        )
        
        # Student progress details
        student_progress = homework_progress.values(
            'student__user__first_name', 'student__user__last_name',
            'student__user__username'
        ).annotate(
            solved_tasks=Count('student__task_progress', filter=Q(
                student__task_progress__task__homework=homework,
                student__task_progress__is_solved=True
            )),
            total_tasks=Count('student__task_progress', filter=Q(
                student__task_progress__task__homework=homework
            )),
            completion_percentage=F('solved_tasks') / F('total_tasks') * 100,
            last_activity=Max('last_attempt_at')
        )
        
        analytics_data = {
            'homework': {
                'id': homework.id,
                'title': homework.title,
                'lesson_title': homework.lesson.title,
                'lesson_id': homework.lesson.id
            },
            'overview': {
                'total_students': total_students,
                'completed_students': completed_students,
                'completion_rate': (completed_students / total_students * 100) if total_students > 0 else 0
            },
            'task_breakdown': list(task_breakdown),
            'student_progress': list(student_progress),
            'completion_timeline': [],  # Can be implemented with time-series data
            'difficulty_metrics': {}  # Can be implemented with difficulty analysis
        }
        
        serializer = HomeworkAnalyticsSerializer(analytics_data)
        return Response(serializer.data)
