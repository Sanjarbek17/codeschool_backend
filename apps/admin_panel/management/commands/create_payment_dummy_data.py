from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.admin_panel.models import Payment
from apps.accounts.models import Student, Group
from apps.courses.models import Course
from faker import Faker
from decimal import Decimal
from datetime import date, timedelta
import random
import calendar

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for Payment models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--months",
            type=int,
            default=6,
            help="Number of months to create payments for",
        )
        parser.add_argument(
            "--base-amount", type=float, default=150.0, help="Base payment amount"
        )

    def handle(self, *args, **options):
        months_count = options["months"]
        base_amount = Decimal(str(options["base_amount"]))

        self.stdout.write("Creating dummy data for Payment models...")

        # Get existing students and groups
        students = list(Student.objects.all())
        groups = list(Group.objects.all())
        courses = list(Course.objects.all())

        if not students:
            self.stdout.write(
                self.style.WARNING(
                    "No students found. Run create_accounts_dummy_data first."
                )
            )
            return

        if not groups:
            self.stdout.write(
                self.style.WARNING(
                    "No groups found. Run create_accounts_dummy_data first."
                )
            )
            return

        # Generate payments for the last N months
        today = timezone.now().date()
        created_payments = []

        self.stdout.write(f"Creating payments for {months_count} months...")

        for i in range(months_count):
            # Calculate month and year (going backwards from current month)
            month_date = today - timedelta(days=30 * i)
            month = month_date.month
            year = month_date.year

            # Get the 15th of the month as due date (or last day if month has < 15 days)
            last_day = calendar.monthrange(year, month)[1]
            due_date = date(year, month, min(15, last_day))

            self.stdout.write(f"  Creating payments for {month:02d}/{year}...")

            # Create payments for students with groups
            month_payments = 0
            for student in students:
                if student.groups.exists():
                    for group in student.groups.all():
                        # Check if payment already exists
                        if Payment.objects.filter(
                            student=student.user, group=group, month=month, year=year
                        ).exists():
                            continue

                        # Vary the payment amount slightly
                        amount = base_amount + Decimal(str(random.uniform(-30, 50)))
                        amount = max(Decimal("50.00"), amount)  # Minimum 50

                        # Choose course (prefer group's current course or random)
                        course = group.current_course
                        if not course and courses:
                            course = random.choice(courses)

                        # Determine payment status based on age of payment
                        if i == 0:  # Current month
                            status_choices = ["pending", "partially_paid", "paid"]
                            weights = [
                                0.3,
                                0.2,
                                0.5,
                            ]  # 50% paid, 20% partial, 30% pending
                        elif i <= 2:  # Last 2 months
                            status_choices = [
                                "pending",
                                "partially_paid",
                                "paid",
                                "overdue",
                            ]
                            weights = [0.1, 0.1, 0.7, 0.1]  # Mostly paid
                        else:  # Older months
                            status_choices = ["paid", "overdue", "cancelled"]
                            weights = [0.85, 0.1, 0.05]  # Mostly paid, some overdue

                        status = random.choices(status_choices, weights=weights)[0]

                        # Set paid amount based on status
                        if status == "paid":
                            paid_amount = amount
                            paid_date = fake.date_between(
                                start_date=due_date - timedelta(days=10),
                                end_date=due_date + timedelta(days=30),
                            )
                        elif status == "partially_paid":
                            paid_amount = (
                                Decimal(str(random.uniform(0.2, 0.8))) * amount
                            )
                            paid_date = None
                        else:  # pending, overdue, cancelled
                            paid_amount = Decimal("0.00")
                            paid_date = None

                        # Payment methods for paid amounts
                        payment_methods = [
                            "cash",
                            "card",
                            "bank_transfer",
                            "mobile_payment",
                        ]
                        payment_method = (
                            random.choice(payment_methods) if paid_amount > 0 else ""
                        )

                        # Create the payment
                        payment = Payment.objects.create(
                            student=student.user,
                            group=group,
                            course=course,
                            amount=amount,
                            paid_amount=paid_amount,
                            due_date=due_date,
                            paid_date=(
                                timezone.make_aware(
                                    timezone.datetime.combine(
                                        paid_date, timezone.datetime.min.time()
                                    )
                                )
                                if paid_date
                                else None
                            ),
                            month=month,
                            year=year,
                            status=status,
                            payment_method=payment_method,
                            notes=(
                                fake.sentence() if random.choice([True, False]) else ""
                            ),
                        )

                        created_payments.append(payment)
                        month_payments += 1

            self.stdout.write(
                f"    Created {month_payments} payments for {month:02d}/{year}"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {len(created_payments)} payments")
        )

        # Show statistics
        self.stdout.write("\nPayment Statistics:")

        status_counts = {}
        total_amount = Decimal("0.00")
        total_paid = Decimal("0.00")

        for payment in created_payments:
            status = payment.status
            status_counts[status] = status_counts.get(status, 0) + 1
            total_amount += payment.amount
            total_paid += payment.paid_amount

        for status, count in status_counts.items():
            percentage = (count / len(created_payments)) * 100
            self.stdout.write(f"  {status.title()}: {count} ({percentage:.1f}%)")

        self.stdout.write(f"\nFinancial Summary:")
        self.stdout.write(f"  Total Amount Due: ${total_amount:,.2f}")
        self.stdout.write(f"  Total Paid: ${total_paid:,.2f}")
        self.stdout.write(f"  Outstanding: ${total_amount - total_paid:,.2f}")
        self.stdout.write(
            f"  Collection Rate: {(total_paid / total_amount * 100):.1f}%"
        )
