from rest_framework import serializers
from .models import Lessons
from apps.accounts.serializers import TeacherProfileSerializer


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for Lessons model.
    Includes teacher information and homework count.
    """
    teacher_names = serializers.ReadOnlyField()
    homework_count = serializers.SerializerMethodField()
    teachers_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Lessons
        fields = [
            'id', 'title', 'description', 'video_url', 'content',
            'teachers', 'teachers_data', 'teacher_names', 'homework_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'teacher_names', 'homework_count']

    def get_homework_count(self, obj):
        """Get the number of homework assignments for this lesson."""
        return obj.get_homework_count()
    
    def get_teachers_data(self, obj):
        """Get detailed teacher information."""
        return [
            {
                'id': teacher.id,
                'full_name': teacher.full_name,
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'phone_number': teacher.phone_number
            }
            for teacher in obj.teachers.all()
        ]


class LessonListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for lesson list views.
    Includes essential information without heavy relationships.
    """
    teacher_names = serializers.ReadOnlyField()
    homework_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lessons
        fields = [
            'id', 'title', 'description', 'teacher_names', 
            'homework_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'teacher_names', 'homework_count']

    def get_homework_count(self, obj):
        """Get the number of homework assignments for this lesson."""
        return obj.get_homework_count()


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating lessons.
    Focused on editable fields only.
    """
    
    class Meta:
        model = Lessons
        fields = [
            'title', 'description', 'video_url', 'content', 'teachers'
        ]

    def validate_title(self, value):
        """Validate lesson title is not empty and unique."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        
        # Check for uniqueness (excluding current instance if updating)
        queryset = Lessons.objects.filter(title__iexact=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A lesson with this title already exists.")
        
        return value.strip()

    def validate_content(self, value):
        """Validate lesson content is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value.strip()

    def validate_video_url(self, value):
        """Validate video URL format if provided."""
        if value and not value.strip():
            return None
        return value


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for lesson detail views.
    Includes all related information and homework data.
    """
    teacher_names = serializers.ReadOnlyField()
    homework_count = serializers.SerializerMethodField()
    teachers_data = serializers.SerializerMethodField()
    homework_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Lessons
        fields = [
            'id', 'title', 'description', 'video_url', 'content',
            'teachers', 'teachers_data', 'teacher_names', 
            'homework_count', 'homework_list',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'teacher_names', 'homework_count']

    def get_homework_count(self, obj):
        """Get the number of homework assignments for this lesson."""
        return obj.get_homework_count()
    
    def get_teachers_data(self, obj):
        """Get detailed teacher information."""
        return [
            {
                'id': teacher.id,
                'user_id': teacher.user.id,
                'username': teacher.user.username,
                'full_name': teacher.full_name,
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'phone_number': teacher.phone_number
            }
            for teacher in obj.teachers.all()
        ]
    
    def get_homework_list(self, obj):
        """Get list of homework assignments for this lesson."""
        homework_assignments = obj.homework_set.all()
        return [
            {
                'id': hw.id,
                'title': hw.title,
                'description': hw.description[:100] + '...' if len(hw.description) > 100 else hw.description,
                'task_count': hw.get_task_count(),
                'created_at': hw.created_at
            }
            for hw in homework_assignments
        ]
