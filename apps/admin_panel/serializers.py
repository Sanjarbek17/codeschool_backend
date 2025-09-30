from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
import random
import string
from datetime import datetime
from .models import Payment, StudentPaymentStatus
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
    remaining_amount = serializers.SerializerMethodField()
    payment_percentage = serializers.SerializerMethodField()
    is_fully_paid = serializers.SerializerMethodField()
    is_partially_paid = serializers.SerializerMethodField()

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
            "paid_amount",
            "remaining_amount",
            "payment_percentage",
            "is_fully_paid",
            "is_partially_paid",
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
        read_only_fields = [
            "created_at",
            "updated_at",
            "is_overdue",
            "days_overdue",
            "remaining_amount",
            "payment_percentage",
            "is_fully_paid",
            "is_partially_paid",
        ]

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

    def get_remaining_amount(self, obj):
        return obj.remaining_amount

    def get_payment_percentage(self, obj):
        return obj.payment_percentage

    def get_is_fully_paid(self, obj):
        return obj.is_fully_paid

    def get_is_partially_paid(self, obj):
        return obj.is_partially_paid


class PartialPaymentSerializer(serializers.Serializer):
    """Serializer for adding partial payments"""

    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    payment_method = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        if hasattr(self, "instance") and self.instance:
            if value > self.instance.remaining_amount:
                raise serializers.ValidationError(
                    f"Amount exceeds remaining balance of {self.instance.remaining_amount}"
                )
        return value


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
            "paid_amount",
            "due_date",
            "status",
            "notes",
            "payment_method",
            "processed_by",
        ]


class StudentPaymentStatusSerializer(serializers.ModelSerializer):
    """Serializer for StudentPaymentStatus model"""

    student_name = serializers.SerializerMethodField()
    unpaid_months = serializers.SerializerMethodField()

    class Meta:
        model = StudentPaymentStatus
        fields = [
            "id",
            "student",
            "student_name",
            "status",
            "consecutive_unpaid_months",
            "unpaid_months",
            "total_debt",
            "last_payment_date",
            "suspension_date",
            "warning_sent_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username

    def get_unpaid_months(self, obj):
        return Payment.get_student_unpaid_months(obj.student)


class StudentAtRiskSerializer(serializers.Serializer):
    """Serializer for students at risk of suspension"""

    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    unpaid_months = serializers.IntegerField()
    total_debt = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_payment_date = serializers.DateField(allow_null=True)
    status = serializers.CharField()
    groups = serializers.ListField(child=serializers.CharField())


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
            "admin_notes",
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


class AdminStudentRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to register new students.
    Auto-generates username and password for simplicity.
    """

    # Profile fields - username and password will be auto-generated
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20)
    parents_phone_number = serializers.CharField(max_length=20)
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, required=False
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "parents_phone_number",
            "admin_notes",
            "groups",
        )

    def _generate_unique_username(self, first_name):
        """Generate a unique username based on first_name."""
        # Clean first_name and make it lowercase
        base_username = first_name.lower().replace(" ", "")

        # Try simple username first
        if not User.objects.filter(username=base_username).exists():
            return base_username

        # Add numbers until we find a unique one
        counter = 1
        while True:
            username = f"{base_username}{counter}"
            if not User.objects.filter(username=username).exists():
                return username
            counter += 1

    def _generate_simple_password(self, first_name):
        """Generate a simple but secure password."""
        # Simple pattern: first_name + current_year + simple suffix
        year = datetime.now().year
        clean_name = first_name.lower().replace(" ", "")
        return f"{clean_name}{year}!"

    def create(self, validated_data):
        """Create user and student profile with auto-generated credentials."""
        # Remove non-user fields
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        phone_number = validated_data.pop("phone_number")
        parents_phone_number = validated_data.pop("parents_phone_number")
        admin_notes = validated_data.pop("admin_notes", "")
        groups = validated_data.pop("groups", [])

        # Generate username and password
        username = self._generate_unique_username(first_name)
        password = self._generate_simple_password(first_name)

        # Add generated credentials to validated_data
        validated_data["username"] = username
        validated_data["password"] = password

        # Create user
        user = User.objects.create_user(**validated_data)

        # Store the plain password for response (before it gets hashed)
        user._plain_password = password

        # Create student profile
        student = Student.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            parents_phone_number=parents_phone_number,
            admin_notes=admin_notes,
        )

        # Add groups if provided
        if groups:
            student.groups.set(groups)

        # Create authentication token
        Token.objects.create(user=user)

        return user


class AdminTeacherRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to register new teachers.
    Auto-generates username and password for simplicity.
    """

    # Profile fields - username and password will be auto-generated
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
        )

    def _generate_unique_username(self, first_name):
        """Generate a unique username based on first_name."""
        # Clean first_name and make it lowercase
        base_username = first_name.lower().replace(" ", "")

        # Try simple username first
        if not User.objects.filter(username=base_username).exists():
            return base_username

        # Add numbers until we find a unique one
        counter = 1
        while True:
            username = f"{base_username}{counter}"
            if not User.objects.filter(username=username).exists():
                return username
            counter += 1

    def _generate_simple_password(self, first_name):
        """Generate a simple but secure password."""
        # Simple pattern: first_name + current_year + simple suffix
        year = datetime.now().year
        clean_name = first_name.lower().replace(" ", "")
        return f"{clean_name}{year}!"

    def create(self, validated_data):
        """Create user and teacher profile with auto-generated credentials."""
        # Remove non-user fields
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        phone_number = validated_data.pop("phone_number")

        # Generate username and password
        username = self._generate_unique_username(first_name)
        password = self._generate_simple_password(first_name)

        # Add generated credentials to validated_data
        validated_data["username"] = username
        validated_data["password"] = password

        # Create user
        user = User.objects.create_user(**validated_data)

        # Store the plain password for response (before it gets hashed)
        user._plain_password = password

        # Create teacher profile
        Teacher.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
        )

        # Create authentication token
        Token.objects.create(user=user)

        return user
