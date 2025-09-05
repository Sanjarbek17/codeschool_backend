from rest_framework import serializers
from apps.accounts.models import Teacher, Student, Group, User


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
