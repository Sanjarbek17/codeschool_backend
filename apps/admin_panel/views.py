from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal

from .models import Payment, StudentPaymentStatus
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentUpdateSerializer,
    PartialPaymentSerializer,
    StudentPaymentSummarySerializer,
    StudentPaymentStatusSerializer,
    StudentAtRiskSerializer,
    StudentManagementSerializer,
    TeacherManagementSerializer,
    GroupManagementSerializer,
    CourseManagementSerializer,
    AdminStudentRegistrationSerializer,
    AdminTeacherRegistrationSerializer,
)
from .permissions import IsAdminUser, IsOwnerOrAdmin
from apps.accounts.models import Teacher, Student, Group
from apps.courses.models import Course, Lessons

User = get_user_model()


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    Provides CRUD operations for payments with admin-only access.
    """

    queryset = Payment.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return PaymentUpdateSerializer
        return PaymentSerializer

    def get_queryset(self):
        queryset = Payment.objects.select_related(
            "student", "group", "course", "processed_by"
        ).all()

        # Filter parameters
        status_filter = self.request.query_params.get("status")
        student_id = self.request.query_params.get("student")
        group_id = self.request.query_params.get("group")
        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")
        overdue_only = self.request.query_params.get("overdue_only")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if group_id:
            queryset = queryset.filter(group_id=group_id)

        if month:
            queryset = queryset.filter(month=month)

        if year:
            queryset = queryset.filter(year=year)

        if overdue_only == "true":
            queryset = queryset.filter(
                status__in=["pending", "overdue"], due_date__lt=timezone.now().date()
            )

        return queryset.order_by("-year", "-month", "due_date")

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        """Mark a payment as paid"""
        payment = self.get_object()

        if payment.status == "paid":
            return Response(
                {"error": "Payment is already marked as paid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_method = request.data.get("payment_method", "")
        notes = request.data.get("notes", "")

        payment.mark_as_paid(
            payment_method=payment_method, processed_by=request.user, notes=notes
        )

        serializer = self.get_serializer(payment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_partial_payment(self, request, pk=None):
        """Add a partial payment to an existing payment record"""
        payment = self.get_object()

        if payment.status == "paid":
            return Response(
                {"error": "Payment is already fully paid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PartialPaymentSerializer(data=request.data, instance=payment)
        if serializer.is_valid():
            try:
                amount = serializer.validated_data["amount"]
                payment_method = serializer.validated_data.get("payment_method", "")
                notes = serializer.validated_data.get("notes", "")

                remaining = payment.add_payment(
                    amount=amount,
                    payment_method=payment_method,
                    processed_by=request.user,
                    notes=notes,
                )

                response_data = PaymentSerializer(payment).data
                response_data["remaining_amount"] = remaining
                response_data["message"] = (
                    f"Partial payment of {amount} added successfully"
                )

                if payment.status == "paid":
                    response_data["message"] = (
                        f"Payment completed with final amount of {amount}"
                    )

                return Response(response_data)

            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def create_monthly_payments(self, request):
        """Create payments for all students for a specific month/year"""
        month = request.data.get("month")
        year = request.data.get("year")
        amount = request.data.get("amount", "100.00")

        if not month or not year:
            return Response(
                {"error": "Month and year are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month = int(month)
            year = int(year)
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid month, year, or amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (1 <= month <= 12):
            return Response(
                {"error": "Month must be between 1 and 12"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_payments = Payment.create_monthly_payments(month, year, amount)

        return Response(
            {
                "message": f"Created {len(created_payments)} payments for {month}/{year}",
                "created_count": len(created_payments),
            }
        )

    @action(detail=False, methods=["post"])
    def update_overdue(self, request):
        """Update all pending payments that are past due to overdue status"""
        updated_count = Payment.update_overdue_payments()

        return Response(
            {
                "message": f"Updated {updated_count} payments to overdue status",
                "updated_count": updated_count,
            }
        )

    @action(detail=False, methods=["get"])
    def payment_statistics(self, request):
        """Get payment statistics overview"""
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year

        # Overall statistics
        total_payments = Payment.objects.count()
        paid_payments = Payment.objects.filter(status="paid").count()
        pending_payments = Payment.objects.filter(status="pending").count()
        overdue_payments = Payment.objects.filter(status="overdue").count()

        # Current month statistics
        current_month_payments = Payment.objects.filter(
            month=current_month, year=current_year
        )
        current_month_total = current_month_payments.count()
        current_month_paid = current_month_payments.filter(status="paid").count()
        current_month_pending = current_month_payments.filter(status="pending").count()
        current_month_overdue = current_month_payments.filter(status="overdue").count()

        # Financial statistics
        total_amount = Payment.objects.aggregate(Sum("amount"))["amount__sum"] or 0
        paid_amount = (
            Payment.objects.filter(status="paid").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        outstanding_amount = total_amount - paid_amount

        return Response(
            {
                "overall": {
                    "total_payments": total_payments,
                    "paid_payments": paid_payments,
                    "pending_payments": pending_payments,
                    "overdue_payments": overdue_payments,
                    "total_amount": total_amount,
                    "paid_amount": paid_amount,
                    "outstanding_amount": outstanding_amount,
                },
                "current_month": {
                    "month": current_month,
                    "year": current_year,
                    "total_payments": current_month_total,
                    "paid_payments": current_month_paid,
                    "pending_payments": current_month_pending,
                    "overdue_payments": current_month_overdue,
                },
            }
        )

    @action(detail=False, methods=["get"])
    def students_at_risk(self, request):
        """Get students who haven't paid for multiple months"""
        min_months = int(request.query_params.get("min_months", 2))

        students_at_risk = Payment.get_students_with_multiple_unpaid_months(min_months)

        # Format data for serializer
        formatted_data = []
        for item in students_at_risk:
            student = item["student"]

            # Get student's groups
            student_profile = getattr(student, "student_profile", None)
            groups = []
            if student_profile:
                groups = [group.name for group in student_profile.groups.all()]

            # Get last payment date
            last_payment = (
                Payment.objects.filter(student=student, status="paid")
                .order_by("-paid_date")
                .first()
            )

            formatted_data.append(
                {
                    "student_id": student.id,
                    "student_name": student.get_full_name() or student.username,
                    "unpaid_months": item["unpaid_months"],
                    "total_debt": item["total_debt"],
                    "last_payment_date": (
                        last_payment.paid_date.date() if last_payment else None
                    ),
                    "status": "At Risk",
                    "groups": groups,
                }
            )

        serializer = StudentAtRiskSerializer(formatted_data, many=True)
        return Response(
            {
                "count": len(formatted_data),
                "students": serializer.data,
                "summary": {
                    "total_at_risk": len(formatted_data),
                    "total_debt": sum(item["total_debt"] for item in students_at_risk),
                    "avg_unpaid_months": (
                        sum(item["unpaid_months"] for item in students_at_risk)
                        / len(students_at_risk)
                        if students_at_risk
                        else 0
                    ),
                },
            }
        )

    @action(detail=False, methods=["get"])
    def suspension_candidates(self, request):
        """Get students who should be suspended for non-payment"""
        candidates = Payment.get_suspension_candidates()

        formatted_data = []
        for item in candidates:
            student = item["student"]
            student_profile = getattr(student, "student_profile", None)
            groups = []
            if student_profile:
                groups = [group.name for group in student_profile.groups.all()]

            last_payment = (
                Payment.objects.filter(student=student, status="paid")
                .order_by("-paid_date")
                .first()
            )

            formatted_data.append(
                {
                    "student_id": student.id,
                    "student_name": student.get_full_name() or student.username,
                    "unpaid_months": item["unpaid_months"],
                    "total_debt": item["total_debt"],
                    "last_payment_date": (
                        last_payment.paid_date.date() if last_payment else None
                    ),
                    "status": "Suspension Candidate",
                    "groups": groups,
                }
            )

        serializer = StudentAtRiskSerializer(formatted_data, many=True)
        return Response(
            {
                "count": len(formatted_data),
                "candidates": serializer.data,
                "message": f"{len(formatted_data)} students should be suspended for non-payment",
            }
        )

    @action(detail=False, methods=["post"])
    def update_all_payment_statuses(self, request):
        """Update payment status for all students"""
        updated_count = StudentPaymentStatus.update_all_statuses()

        return Response(
            {
                "message": f"Updated payment status for {updated_count} students",
                "updated_count": updated_count,
            }
        )


class StudentPaymentSummaryView(APIView):
    """
    View to get payment summary for a specific student.
    Accessible by admin users or the student themselves.
    """

    permission_classes = [IsOwnerOrAdmin]

    def get(self, request, student_id):
        try:
            user = User.objects.get(id=student_id)

            # Check permissions
            if not (
                request.user.is_staff
                or request.user.is_superuser
                or request.user == user
            ):
                return Response(
                    {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                )

            summary = Payment.get_student_payment_summary(user)
            summary["student_id"] = user.id
            summary["student_name"] = user.get_full_name() or user.username

            serializer = StudentPaymentSummarySerializer(summary)
            return Response(serializer.data)

        except User.DoesNotExist:
            return Response(
                {"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND
            )


class AdminDashboardView(APIView):
    """
    Main dashboard view for admin panel with overview statistics.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        # Student statistics
        total_students = Student.objects.count()
        active_students = (
            Student.objects.filter(groups__isnull=False).distinct().count()
        )

        # Teacher statistics
        total_teachers = Teacher.objects.count()
        active_teachers = (
            Teacher.objects.filter(groups__isnull=False).distinct().count()
        )

        # Group statistics
        total_groups = Group.objects.count()
        active_groups = Group.objects.filter(students__isnull=False).distinct().count()

        # Course statistics
        total_courses = Course.objects.count()
        active_courses = Course.objects.filter(is_active=True).count()

        # Payment statistics
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year

        total_payments_this_month = Payment.objects.filter(
            month=current_month, year=current_year
        ).count()

        overdue_payments = Payment.objects.filter(
            status__in=["pending", "overdue"], due_date__lt=today
        ).count()

        total_outstanding_amount = (
            Payment.objects.filter(status__in=["pending", "overdue"]).aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )

        return Response(
            {
                "students": {"total": total_students, "active": active_students},
                "teachers": {"total": total_teachers, "active": active_teachers},
                "groups": {"total": total_groups, "active": active_groups},
                "courses": {"total": total_courses, "active": active_courses},
                "payments": {
                    "this_month_total": total_payments_this_month,
                    "overdue_count": overdue_payments,
                    "outstanding_amount": total_outstanding_amount,
                },
            }
        )


class StudentManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing students in admin panel.
    """

    queryset = Student.objects.select_related("user").prefetch_related("groups").all()
    serializer_class = StudentManagementSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter parameters
        search = self.request.query_params.get("search")
        group_id = self.request.query_params.get("group")
        has_overdue = self.request.query_params.get("has_overdue")

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(user__username__icontains=search)
                | Q(phone_number__icontains=search)
            )

        if group_id:
            queryset = queryset.filter(groups__id=group_id)

        if has_overdue == "true":
            overdue_student_ids = (
                Payment.objects.filter(status="overdue")
                .values_list("student_id", flat=True)
                .distinct()
            )
            queryset = queryset.filter(user_id__in=overdue_student_ids)

        return queryset.order_by("last_name", "first_name")


class TeacherManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing teachers in admin panel.
    """

    queryset = (
        Teacher.objects.select_related("user")
        .prefetch_related("groups", "courses")
        .all()
    )
    serializer_class = TeacherManagementSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter parameters
        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(user__username__icontains=search)
                | Q(phone_number__icontains=search)
            )

        return queryset.order_by("last_name", "first_name")


class GroupManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing groups in admin panel.
    """

    queryset = (
        Group.objects.select_related("current_course", "current_lesson")
        .prefetch_related("teachers", "students")
        .all()
    )
    serializer_class = GroupManagementSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter parameters
        search = self.request.query_params.get("search")
        course_id = self.request.query_params.get("course")
        teacher_id = self.request.query_params.get("teacher")

        if search:
            queryset = queryset.filter(name__icontains=search)

        if course_id:
            queryset = queryset.filter(current_course_id=course_id)

        if teacher_id:
            queryset = queryset.filter(teachers__id=teacher_id)

        return queryset.order_by("name")


class CourseManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing courses in admin panel.
    """

    queryset = Course.objects.prefetch_related("teachers").all()
    serializer_class = CourseManagementSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter parameters
        search = self.request.query_params.get("search")
        level = self.request.query_params.get("level")
        is_active = self.request.query_params.get("is_active")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        if level:
            queryset = queryset.filter(level=level)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset.order_by("title")


class StudentPaymentStatusViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student payment statuses and restrictions.
    """

    queryset = StudentPaymentStatus.objects.select_related("student").all()
    serializer_class = StudentPaymentStatusSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter parameters
        status_filter = self.request.query_params.get("status")
        min_debt = self.request.query_params.get("min_debt")
        min_unpaid_months = self.request.query_params.get("min_unpaid_months")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if min_debt:
            try:
                min_debt = Decimal(str(min_debt))
                queryset = queryset.filter(total_debt__gte=min_debt)
            except (ValueError, TypeError):
                pass

        if min_unpaid_months:
            try:
                min_unpaid_months = int(min_unpaid_months)
                queryset = queryset.filter(
                    consecutive_unpaid_months__gte=min_unpaid_months
                )
            except (ValueError, TypeError):
                pass

        return queryset.order_by("-consecutive_unpaid_months", "-total_debt")

    @action(detail=False, methods=["post"])
    def update_all_statuses(self, request):
        """Update payment status for all students"""
        updated_count = StudentPaymentStatus.update_all_statuses()

        return Response(
            {
                "message": f"Updated payment status for {updated_count} students",
                "updated_count": updated_count,
            }
        )

    @action(detail=True, methods=["post"])
    def send_warning(self, request, pk=None):
        """Send payment warning to student"""
        payment_status = self.get_object()

        # Here you would integrate with your notification system
        # For now, just update the warning_sent_date
        payment_status.warning_sent_date = timezone.now().date()
        payment_status.save()

        return Response(
            {
                "message": f"Warning sent to {payment_status.student.get_full_name()}",
                "warning_sent_date": payment_status.warning_sent_date,
            }
        )

    @action(detail=True, methods=["post"])
    def suspend_student(self, request, pk=None):
        """Suspend student for non-payment"""
        payment_status = self.get_object()

        if payment_status.consecutive_unpaid_months >= 3:
            payment_status.status = "suspended"
            payment_status.suspension_date = timezone.now().date()
            payment_status.save()

            return Response(
                {
                    "message": f"Student {payment_status.student.get_full_name()} suspended for non-payment",
                    "suspension_date": payment_status.suspension_date,
                }
            )
        else:
            return Response(
                {"error": "Student must have 3+ unpaid months to be suspended"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def reactivate_student(self, request, pk=None):
        """Reactivate suspended student"""
        payment_status = self.get_object()

        if payment_status.status in ["suspended", "warning"]:
            payment_status.status = "active"
            payment_status.suspension_date = None
            payment_status.warning_sent_date = None
            payment_status.save()

            return Response(
                {
                    "message": f"Student {payment_status.student.get_full_name()} reactivated"
                }
            )
        else:
            return Response(
                {"error": "Student is not suspended or warned"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AdminStudentRegistrationView(APIView):
    """
    Admin endpoint for registering new students.
    Only accessible by admin users.
    """

    permission_classes = [IsAdminUser]

    def post(self, request):
        """Register a new student account with auto-generated credentials."""
        serializer = AdminStudentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            student = user.student_profile

            # Get the generated plain password
            generated_password = getattr(user, "_plain_password", None)

            return Response(
                {
                    "message": "Student registered successfully",
                    "credentials": {
                        "username": user.username,
                        "password": generated_password,
                        "note": "Please provide these credentials to the student. They can change them later.",
                    },
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                    "student": {
                        "id": student.id,
                        "first_name": student.first_name,
                        "last_name": student.last_name,
                        "phone_number": student.phone_number,
                        "parents_phone_number": student.parents_phone_number,
                        "groups": [group.id for group in student.groups.all()],
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminTeacherRegistrationView(APIView):
    """
    Admin endpoint for registering new teachers.
    Only accessible by admin users.
    """

    permission_classes = [IsAdminUser]

    def post(self, request):
        """Register a new teacher account with auto-generated credentials."""
        serializer = AdminTeacherRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            teacher = user.teacher_profile

            # Get the generated plain password
            generated_password = getattr(user, "_plain_password", None)

            return Response(
                {
                    "message": "Teacher registered successfully",
                    "credentials": {
                        "username": user.username,
                        "password": generated_password,
                        "note": "Please provide these credentials to the teacher. They can change them later.",
                    },
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                    "teacher": {
                        "id": teacher.id,
                        "first_name": teacher.first_name,
                        "last_name": teacher.last_name,
                        "phone_number": teacher.phone_number,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
