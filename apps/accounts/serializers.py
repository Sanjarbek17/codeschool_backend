from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
from .models import User, Teacher, Student, Group


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles password confirmation and validation.
    """

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    user_type = serializers.ChoiceField(
        choices=[("teacher", "Teacher"), ("student", "Student")], write_only=True
    )

    # Profile fields
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20)
    parents_phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Required for students only",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "user_type",
            "first_name",
            "last_name",
            "phone_number",
            "parents_phone_number",
        )

    def validate(self, attrs):
        """Validate password confirmation and user type specific fields."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                "Password and password confirmation don't match."
            )

        # Validate student-specific fields
        if attrs["user_type"] == "student" and not attrs.get("parents_phone_number"):
            raise serializers.ValidationError(
                "Parent's phone number is required for students."
            )

        return attrs

    def create(self, validated_data):
        """Create user and associated profile (Teacher or Student)."""
        # Remove non-user fields
        password_confirm = validated_data.pop("password_confirm")
        user_type = validated_data.pop("user_type")
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        phone_number = validated_data.pop("phone_number")
        parents_phone_number = validated_data.pop("parents_phone_number", "")

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create profile based on user type
        if user_type == "teacher":
            Teacher.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
            )
        elif user_type == "student":
            Student.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                parents_phone_number=parents_phone_number,
            )

        # Create authentication token
        Token.objects.create(user=user)

        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Authenticates user and returns token.
    """

    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        """Authenticate user credentials."""
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(
                request=self.context.get("request"),
                username=username,
                password=password,
            )

            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )

            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")

            attrs["user"] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "username" and "password".')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    Includes profile data from Teacher or Student models.
    """

    profile_type = serializers.SerializerMethodField()
    profile_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "profile_type",
            "profile_data",
        )
        read_only_fields = ("id", "username", "date_joined")

    def get_profile_type(self, obj):
        """Determine if user is a teacher or student."""
        if hasattr(obj, "teacher_profile"):
            return "teacher"
        elif hasattr(obj, "student_profile"):
            return "student"
        return None

    def get_profile_data(self, obj):
        """Get profile data based on user type."""
        if hasattr(obj, "teacher_profile"):
            return TeacherProfileSerializer(obj.teacher_profile).data
        elif hasattr(obj, "student_profile"):
            return StudentProfileSerializer(obj.student_profile).data
        return None


class TeacherProfileSerializer(serializers.ModelSerializer):
    """Serializer for Teacher profile data."""

    class Meta:
        model = Teacher
        fields = ("first_name", "last_name", "phone_number", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for Student profile data."""

    groups_data = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "parents_phone_number",
            "groups",
            "groups_data",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_groups_data(self, obj):
        """Get detailed group information."""
        return [
            {"id": group.id, "name": group.name, "teacher_count": group.teacher_count}
            for group in obj.groups.all()
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """

    old_password = serializers.CharField(style={"input_type": "password"})
    new_password = serializers.CharField(
        validators=[validate_password], style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        """Validate password change request."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                "New password and confirmation don't match."
            )
        return attrs

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for Group model.
    Includes teacher and student information.
    """

    teacher_count = serializers.ReadOnlyField()
    student_count = serializers.ReadOnlyField()
    teachers_data = serializers.SerializerMethodField()
    students_data = serializers.SerializerMethodField()
    lessons_data = serializers.SerializerMethodField()
    current_lesson_info = serializers.ReadOnlyField()
    current_course_info = serializers.ReadOnlyField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "created_date",
            "updated_at",
            "teachers",
            "teachers_data",
            "teacher_count",
            "students_data",
            "student_count",
            "lessons_data",
            "current_course",
            "current_course_info",
            "current_lesson",
            "current_lesson_info",
            "last_taught_date",
        ]
        read_only_fields = ["created_date", "updated_at"]

    def get_teachers_data(self, obj):
        """Get detailed teacher information."""
        return [
            {
                "id": teacher.id,
                "full_name": teacher.full_name,
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "phone_number": teacher.phone_number,
            }
            for teacher in obj.teachers.all()
        ]

    def get_students_data(self, obj):
        """Get detailed student information."""
        return [
            {
                "id": student.id,
                "full_name": student.full_name,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "phone_number": student.phone_number,
            }
            for student in obj.students.all()
        ]

    def get_lessons_data(self, obj):
        """Get detailed lessons information for this group by current course."""
        if obj.current_course:
            # Get lessons from the current course, ordered by lesson order
            lessons = obj.current_course.lessons.all().order_by("order")

            return [
                {
                    "id": lesson.id,
                    "title": lesson.title,
                    "description": lesson.description,
                    "video_url": lesson.video_url,
                    "order": lesson.order,
                    "teacher_names": lesson.teacher_names,
                    "created_at": lesson.created_at,
                }
                for lesson in lessons
            ]
        return []


class GroupListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for group list views.
    """

    teacher_count = serializers.ReadOnlyField()
    student_count = serializers.ReadOnlyField()

    class Meta:
        model = Group
        fields = ["id", "name", "created_date", "teacher_count", "student_count"]


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating groups.
    """

    class Meta:
        model = Group
        fields = ["name", "teachers", "current_course", "current_lesson"]

    def validate_name(self, value):
        """Validate group name is not empty and unique."""
        if not value.strip():
            raise serializers.ValidationError("Group name cannot be empty.")

        # Check for uniqueness (excluding current instance if updating)
        queryset = Group.objects.filter(name__iexact=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("A group with this name already exists.")

        return value.strip()
