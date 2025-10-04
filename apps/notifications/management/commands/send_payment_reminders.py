from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.notifications.utils import create_payment_notification
from apps.accounts.models import Student, Teacher
import random


class Command(BaseCommand):
    help = "Send payment reminder notifications to admin users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            choices=["tuition", "salary", "overdue", "all"],
            default="all",
            help="Type of payment reminders to send",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending notifications",
        )

    def handle(self, *args, **options):
        payment_type = options["type"]
        dry_run = options["dry_run"]

        notifications_sent = 0

        self.stdout.write(
            self.style.SUCCESS(
                f"Generating payment reminders of type: {payment_type}..."
            )
        )

        if payment_type in ["tuition", "all"]:
            # Send tuition payment reminders
            students = Student.objects.all()[:5]  # Limit for demo

            for student in students:
                if not dry_run:
                    create_payment_notification(
                        title=f"Tuition Payment Reminder: {student.full_name}",
                        message=f"Monthly tuition payment for {student.full_name} is due in 3 days. "
                        f"Amount: $500.00",
                        payment_type="tuition",
                        payment_status="pending",
                        amount=500.00,
                        currency="USD",
                        student=student,
                        due_date=timezone.now() + timedelta(days=3),
                    )
                    notifications_sent += 1
                else:
                    self.stdout.write(
                        f"Would send tuition reminder for {student.full_name}"
                    )
                    notifications_sent += 1

        if payment_type in ["salary", "all"]:
            # Send salary payment notifications
            teachers = Teacher.objects.all()[:3]  # Limit for demo

            for teacher in teachers:
                if not dry_run:
                    create_payment_notification(
                        title=f"Salary Payment: {teacher.full_name}",
                        message=f"Monthly salary payment for {teacher.full_name} has been processed. "
                        f"Amount: $2000.00",
                        payment_type="salary",
                        payment_status="completed",
                        amount=2000.00,
                        currency="USD",
                        teacher=teacher,
                        paid_at=timezone.now(),
                    )
                    notifications_sent += 1
                else:
                    self.stdout.write(
                        f"Would send salary notification for {teacher.full_name}"
                    )
                    notifications_sent += 1

        if payment_type in ["overdue", "all"]:
            # Send overdue payment notifications
            overdue_students = Student.objects.all()[:2]  # Limit for demo

            for student in overdue_students:
                if not dry_run:
                    create_payment_notification(
                        title=f"OVERDUE: Payment Required - {student.full_name}",
                        message=f"Payment for {student.full_name} is now overdue by 15 days. "
                        f"Please contact the student immediately. Amount: $500.00",
                        payment_type="tuition",
                        payment_status="overdue",
                        amount=500.00,
                        currency="USD",
                        student=student,
                        due_date=timezone.now() - timedelta(days=15),
                    )
                    notifications_sent += 1
                else:
                    self.stdout.write(
                        f"Would send overdue payment notice for {student.full_name}"
                    )
                    notifications_sent += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would send {notifications_sent} payment notifications"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully sent {notifications_sent} payment notifications to admin"
                )
            )
