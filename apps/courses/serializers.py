from rest_framework import serializers
from .models import Course, Lessons, Attendance
from apps.accounts.serializers import TeacherProfileSerializer


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model.
    Includes teacher information and lesson count.
    """

    teacher_names = serializers.ReadOnlyField()
    lesson_count = serializers.ReadOnlyField()
    teachers_data = serializers.SerializerMethodField()
    lessons_data = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "duration_weeks",
            "level",
            "is_active",
            "teachers",
            "teachers_data",
            "teacher_names",
            "lesson_count",
            "lessons_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "teacher_names",
            "lesson_count",
        ]

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

    def get_lessons_data(self, obj):
        """Get basic lesson information for this course."""
        return [
            {
                "id": lesson.id,
                "title": lesson.title,
                "order": lesson.order,
                "video_url": lesson.video_url,
            }
            for lesson in obj.lessons.all().order_by("order")
        ]


class CourseListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for course list views.
    """

    teacher_names = serializers.ReadOnlyField()
    lesson_count = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "duration_weeks",
            "level",
            "is_active",
            "teacher_names",
            "lesson_count",
            "created_at",
        ]


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for Lessons model.
    Includes teacher information, course information, and homework count.
    """

    teacher_names = serializers.ReadOnlyField()
    homework_count = serializers.SerializerMethodField()
    teachers_data = serializers.SerializerMethodField()
    course_data = serializers.SerializerMethodField()

    class Meta:
        model = Lessons
        fields = [
            "id",
            "title",
            "description",
            "video_url",
            "content",
            "course",
            "course_data",
            "order",
            "teachers",
            "teachers_data",
            "teacher_names",
            "homework_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "teacher_names",
            "homework_count",
        ]

    def get_homework_count(self, obj):
        """Get the number of homework assignments for this lesson."""
        return obj.get_homework_count()

    def get_course_data(self, obj):
        """Get basic course information."""
        if obj.course:
            return {
                "id": obj.course.id,
                "title": obj.course.title,
                "level": obj.course.level,
                "duration_weeks": obj.course.duration_weeks,
            }
        return None

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
            "id",
            "title",
            "description",
            "teacher_names",
            "homework_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "teacher_names",
            "homework_count",
        ]

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
        fields = ["title", "description", "video_url", "content", "teachers"]

    def validate_title(self, value):
        """Validate lesson title is not empty and unique."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")

        # Check for uniqueness (excluding current instance if updating)
        queryset = Lessons.objects.filter(title__iexact=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A lesson with this title already exists."
            )

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
            "id",
            "title",
            "description",
            "video_url",
            "content",
            "teachers",
            "teachers_data",
            "teacher_names",
            "homework_count",
            "homework_list",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "teacher_names",
            "homework_count",
        ]

    def get_homework_count(self, obj):
        """Get the number of homework assignments for this lesson."""
        return obj.get_homework_count()

    def get_teachers_data(self, obj):
        """Get detailed teacher information."""
        return [
            {
                "id": teacher.id,
                "user_id": teacher.user.id,
                "username": teacher.user.username,
                "full_name": teacher.full_name,
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "phone_number": teacher.phone_number,
            }
            for teacher in obj.teachers.all()
        ]

    def get_homework_list(self, obj):
        """Get list of homework assignments for this lesson."""
        homework_assignments = obj.homework_set.all()
        return [
            {
                "id": hw.id,
                "title": hw.title,
                "description": (
                    hw.description[:100] + "..."
                    if len(hw.description) > 100
                    else hw.description
                ),
                "task_count": hw.get_task_count(),
                "created_at": hw.created_at,
            }
            for hw in homework_assignments
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for Attendance model.
    Includes student, lesson, group, and teacher information.
    """

    student_name = serializers.CharField(source="student.full_name", read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_present = serializers.ReadOnlyField()

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "student_name",
            "lesson",
            "lesson_title",
            "group",
            "group_name",
            "teacher",
            "teacher_name",
            "status",
            "status_display",
            "date",
            "notes",
            "is_present",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        """Validate that student belongs to group and teacher can teach the group."""
        student = data.get("student")
        group = data.get("group")
        teacher = data.get("teacher")

        if student and group and student not in group.students.all():
            raise serializers.ValidationError(
                f"Student {student.full_name} is not enrolled in group {group.name}"
            )

        if teacher and group and teacher not in group.teachers.all():
            raise serializers.ValidationError(
                f"Teacher {teacher.full_name} is not assigned to group {group.name}"
            )

        return data


class AttendanceListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for attendance list views.
    """

    student_name = serializers.CharField(source="student.full_name", read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student_name",
            "lesson_title",
            "group_name",
            "status",
            "status_display",
            "date",
            "created_at",
        ]


class AttendanceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating attendance records.
    """

    class Meta:
        model = Attendance
        fields = ["student", "lesson", "group", "teacher", "status", "date", "notes"]

    def validate(self, data):
        """Validate attendance data."""
        student = data.get("student")
        group = data.get("group")
        teacher = data.get("teacher")
        lesson = data.get("lesson")
        date = data.get("date")

        # Check if student belongs to group
        if student and group and student not in group.students.all():
            raise serializers.ValidationError(
                f"Student {student.full_name} is not enrolled in group {group.name}"
            )

        # Check if teacher can teach the group
        if teacher and group and teacher not in group.teachers.all():
            raise serializers.ValidationError(
                f"Teacher {teacher.full_name} is not assigned to group {group.name}"
            )

        # Check for duplicate attendance record
        if not self.instance:  # Only check for creation, not updates
            existing = Attendance.objects.filter(
                student=student, lesson=lesson, group=group, date=date
            ).first()

            if existing:
                raise serializers.ValidationError(
                    f"Attendance record already exists for {student.full_name} "
                    f"in {lesson.title} on {date}"
                )

        return data
