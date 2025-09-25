from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from apps.admin_panel.models import StudentPaymentStatus, Payment
from apps.accounts.models import Student
from faker import Faker
from decimal import Decimal
from datetime import date, timedelta
import random

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for StudentPaymentStatus models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update status for all existing students based on their payment history",
        )

    def handle(self, *args, **options):
        update_existing = options["update_existing"]

        self.stdout.write("Creating dummy data for StudentPaymentStatus models...")

        # Get existing students
        students = list(Student.objects.all())

        if not students:
            self.stdout.write(
                self.style.WARNING(
                    "No students found. Run create_accounts_dummy_data first."
                )
            )
            return

        if update_existing:
            # Update status based on actual payment data
            self.stdout.write(
                "Updating payment status based on actual payment history..."
            )
            updated_count = StudentPaymentStatus.update_all_statuses()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated payment status for {updated_count} students"
                )
            )
            return

        # Create payment status records for students
        self.stdout.write(
            f"Creating payment status records for {len(students)} students..."
        )
        created_statuses = []

        for student in students:
            # Check if student payment status already exists
            if StudentPaymentStatus.objects.filter(student=student.user).exists():
                continue

            # Get student's payment history
            payments = Payment.objects.filter(student=student.user)

            if payments.exists():
                # Calculate actual statistics
                unpaid_months = Payment.get_student_unpaid_months(student.user)
                total_debt = payments.filter(
                    status__in=["pending", "overdue", "partially_paid"]
                ).aggregate(
                    debt=models.Sum(models.F("amount") - models.F("paid_amount"))
                )[
                    "debt"
                ] or Decimal(
                    "0.00"
                )

                # Get last payment date
                last_paid_payment = (
                    payments.filter(status="paid").order_by("-paid_date").first()
                )
                last_payment_date = (
                    last_paid_payment.paid_date.date() if last_paid_payment else None
                )

                # Determine status based on unpaid months
                if unpaid_months >= 4:
                    status = "expelled"
                    suspension_date = fake.date_between(
                        start_date=date.today() - timedelta(days=30),
                        end_date=date.today(),
                    )
                    warning_sent_date = fake.date_between(
                        start_date=date.today() - timedelta(days=60),
                        end_date=date.today() - timedelta(days=30),
                    )
                elif unpaid_months >= 3:
                    status = "suspended"
                    suspension_date = fake.date_between(
                        start_date=date.today() - timedelta(days=20),
                        end_date=date.today(),
                    )
                    warning_sent_date = fake.date_between(
                        start_date=date.today() - timedelta(days=40),
                        end_date=date.today() - timedelta(days=20),
                    )
                elif unpaid_months >= 2:
                    status = "warning"
                    suspension_date = None
                    warning_sent_date = fake.date_between(
                        start_date=date.today() - timedelta(days=15),
                        end_date=date.today(),
                    )
                else:
                    status = "active"
                    suspension_date = None
                    warning_sent_date = None

            else:
                # No payments found, create default active status
                unpaid_months = 0
                total_debt = Decimal("0.00")
                last_payment_date = None
                status = "active"
                suspension_date = None
                warning_sent_date = None

            # Generate notes based on status
            notes_options = {
                "active": [
                    "Student payments are up to date",
                    "Good payment history",
                    "No payment issues",
                    "",
                ],
                "warning": [
                    "Student has missed recent payments",
                    "Payment reminder sent",
                    "Requires follow-up on overdue payments",
                    "Parent contacted regarding payment",
                ],
                "suspended": [
                    "Suspended due to consecutive unpaid months",
                    "Access restricted until payment is made",
                    "Multiple payment reminders sent",
                    "Requires immediate payment to restore access",
                ],
                "expelled": [
                    "Expelled due to extended non-payment",
                    "Account permanently suspended",
                    "Multiple attempts to collect payment failed",
                    "Referred to collections",
                ],
            }

            notes = random.choice(notes_options[status])

            # Create StudentPaymentStatus
            payment_status = StudentPaymentStatus.objects.create(
                student=student.user,
                status=status,
                consecutive_unpaid_months=unpaid_months,
                total_debt=total_debt,
                last_payment_date=last_payment_date,
                suspension_date=suspension_date,
                warning_sent_date=warning_sent_date,
                notes=notes,
            )

            created_statuses.append(payment_status)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(created_statuses)} payment status records"
            )
        )

        # Show statistics
        if created_statuses:
            self.stdout.write("\nPayment Status Distribution:")

            status_counts = {}
            total_debt = Decimal("0.00")

            for payment_status in created_statuses:
                status = payment_status.status
                status_counts[status] = status_counts.get(status, 0) + 1
                total_debt += payment_status.total_debt

            for status, count in status_counts.items():
                percentage = (count / len(created_statuses)) * 100
                self.stdout.write(f"  {status.title()}: {count} ({percentage:.1f}%)")

            self.stdout.write(f"\nTotal Outstanding Debt: ${total_debt:,.2f}")

            # Show students at risk
            at_risk_students = [
                ps
                for ps in created_statuses
                if ps.status in ["warning", "suspended", "expelled"]
            ]
            if at_risk_students:
                self.stdout.write(f"\nStudents at Risk: {len(at_risk_students)}")
                for ps in at_risk_students[:5]:
                    self.stdout.write(
                        f"  - {ps.student.get_full_name()}: {ps.status} "
                        f"({ps.consecutive_unpaid_months} months, ${ps.total_debt})"
                    )
                if len(at_risk_students) > 5:
                    self.stdout.write(f"  ... and {len(at_risk_students) - 5} more")
