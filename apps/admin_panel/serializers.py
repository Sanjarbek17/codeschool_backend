from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Payment
from apps.accounts.models import Teacher, Student, Group
from apps.courses.models import Course, Lessons

User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""

    student_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    payment_period = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "student",
            "student_name",
            "group",
            "group_name",
            "course",
            "course_name",
            "amount",
            "due_date",
            "paid_date",
            "month",
            "year",
            "payment_period",
            "status",
            "notes",
            "payment_method",
            "processed_by",
            "is_overdue",
            "days_overdue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "is_overdue", "days_overdue"]

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username

    def get_group_name(self, obj):
        return obj.group.name

    def get_course_name(self, obj):
        return obj.course.title if obj.course else None

    def get_payment_period(self, obj):
        return obj.payment_period

    def get_is_overdue(self, obj):
        return obj.is_overdue

    def get_days_overdue(self, obj):
        return obj.days_overdue


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments"""

    class Meta:
        model = Payment
        fields = [
            "student",
            "group",
            "course",
            "amount",
            "due_date",
            "month",
            "year",
            "status",
            "notes",
            "payment_method",
        ]

    def validate(self, data):
        # Ensure no duplicate payment for same student/group/month/year
        if Payment.objects.filter(
            student=data["student"],
            group=data["group"],
            month=data["month"],
            year=data["year"],
        ).exists():
            raise serializers.ValidationError(
                "Payment already exists for this student/group/month/year combination."
            )
        return data


class PaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payments"""

    class Meta:
        model = Payment
        fields = [
            "amount",
            "due_date",
            "status",
            "notes",
            "payment_method",
            "processed_by",
        ]


class StudentPaymentSummarySerializer(serializers.Serializer):
    """Serializer for student payment summary"""

    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    total_payments = serializers.IntegerField()
    total_amount_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    total_paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


# Admin Panel Management Serializers


class StudentManagementSerializer(serializers.ModelSerializer):
    """Serializer for student management in admin panel"""

    full_name = serializers.SerializerMethodField()
    groups_count = serializers.SerializerMethodField()
    active_payments = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "parents_phone_number",
            "groups",
            "groups_count",
            "active_payments",
            "created_at",
            "updated_at",
        ]

    def get_full_name(self, obj):
        return obj.full_name

    def get_groups_count(self, obj):
        return obj.groups.count()

    def get_active_payments(self, obj):
        return Payment.objects.filter(
            student=obj.user, status__in=["pending", "overdue"]
        ).count()


class TeacherManagementSerializer(serializers.ModelSerializer):
    """Serializer for teacher management in admin panel"""

    full_name = serializers.SerializerMethodField()
    groups_count = serializers.SerializerMethodField()
    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "groups",
            "groups_count",
            "courses_count",
            "created_at",
            "updated_at",
        ]

    def get_full_name(self, obj):
        return obj.full_name

    def get_groups_count(self, obj):
        return obj.groups.count()

    def get_courses_count(self, obj):
        return obj.courses.count()


class GroupManagementSerializer(serializers.ModelSerializer):
    """Serializer for group management in admin panel"""

    student_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()
    current_course_title = serializers.SerializerMethodField()
    current_lesson_title = serializers.SerializerMethodField()
    total_payments = serializers.SerializerMethodField()
    outstanding_payments = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "created_date",
            "teachers",
            "current_course",
            "current_lesson",
            "last_taught_date",
            "student_count",
            "teacher_count",
            "current_course_title",
            "current_lesson_title",
            "total_payments",
            "outstanding_payments",
            "updated_at",
        ]

    def get_student_count(self, obj):
        return obj.student_count

    def get_teacher_count(self, obj):
        return obj.teacher_count

    def get_current_course_title(self, obj):
        return obj.current_course.title if obj.current_course else None

    def get_current_lesson_title(self, obj):
        return obj.current_lesson.title if obj.current_lesson else None

    def get_total_payments(self, obj):
        return Payment.objects.filter(group=obj).count()

    def get_outstanding_payments(self, obj):
        return Payment.objects.filter(
            group=obj, status__in=["pending", "overdue"]
        ).count()


class CourseManagementSerializer(serializers.ModelSerializer):
    """Serializer for course management in admin panel"""

    lesson_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()
    groups_using_course = serializers.SerializerMethodField()

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
            "lesson_count",
            "teacher_count",
            "groups_using_course",
            "created_at",
            "updated_at",
        ]

    def get_lesson_count(self, obj):
        return obj.lesson_count

    def get_teacher_count(self, obj):
        return obj.teachers.count()

    def get_groups_using_course(self, obj):
        return obj.current_groups.count()
