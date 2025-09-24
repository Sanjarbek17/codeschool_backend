from rest_framework import serializers
from apps.accounts.models import Teacher, Student, Group, User, Schedule, Schedule


class TeacherGroupSerializer(serializers.ModelSerializer):
    """Serializer for groups that a teacher teaches"""

    student_count = serializers.ReadOnlyField()
    teacher_count = serializers.ReadOnlyField()

    class Meta:
        model = Group
        fields = ["id", "name", "created_date", "student_count", "teacher_count"]


class StudentBasicSerializer(serializers.ModelSerializer):
    """Basic student information for teacher views"""

    full_name = serializers.ReadOnlyField()
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "parents_phone_number",
            "user_username",
            "user_email",
            "created_at",
        ]


class TeacherGroupDetailSerializer(serializers.ModelSerializer):
    """Detailed group information including students"""

    students = StudentBasicSerializer(many=True, read_only=True)
    student_count = serializers.ReadOnlyField()

    class Meta:
        model = Group
        fields = ["id", "name", "created_date", "students", "student_count"]


class TeacherDashboardSerializer(serializers.Serializer):
    """Serializer for teacher dashboard summary data"""

    teacher_info = serializers.DictField()
    total_groups = serializers.IntegerField()
    total_students = serializers.IntegerField()
    groups = TeacherGroupSerializer(many=True)
    recent_students = StudentBasicSerializer(many=True)


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for individual schedule entries"""

    group_name = serializers.CharField(source="group.name", read_only=True)
    current_course = serializers.CharField(
        source="group.current_course.title", read_only=True
    )
    current_lesson = serializers.CharField(
        source="group.current_lesson.title", read_only=True
    )
    calculated_end_date = serializers.ReadOnlyField()
    remaining_weeks = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            "id",
            "group_name",
            "day_of_week",
            "start_time",
            "end_time",
            "start_date",
            "end_date",
            "calculated_end_date",
            "remaining_weeks",
            "current_course",
            "current_lesson",
            "is_active",
        ]

    def get_remaining_weeks(self, obj):
        return obj.get_remaining_weeks()


class TeacherWeekScheduleSerializer(serializers.Serializer):
    """Serializer for weekly schedule response"""

    week_start = serializers.DateField(read_only=True)
    week_end = serializers.DateField(read_only=True)
    schedule = serializers.DictField(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
    navigation = serializers.DictField(read_only=True, required=False)


class TeacherMultiWeekScheduleSerializer(serializers.Serializer):
    """Serializer for multi-week schedule response"""

    view_type = serializers.CharField(read_only=True)
    weeks_count = serializers.IntegerField(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    schedule = serializers.DictField(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
