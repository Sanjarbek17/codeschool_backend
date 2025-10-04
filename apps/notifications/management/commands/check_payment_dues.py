from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.notifications.utils import create_payment_notification
from apps.admin_panel.models import Payment  # Use existing Payment model
import calendar


class Command(BaseCommand):
    help = "Send smart payment reminders based on actual Payment model due dates"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-ahead",
            type=int,
            default=3,
            help="Notify X days before payment due (default: 3)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending",
        )

    def handle(self, *args, **options):
        days_ahead = options["days_ahead"]
        dry_run = options["dry_run"]

        today = timezone.now().date()
        reminder_date = today + timedelta(days=days_ahead)

        notifications_sent = 0

        self.stdout.write(self.style.SUCCESS(f"Checking payments for {today}..."))

        # Check payments due soon (3 days ahead)
        upcoming_payments = Payment.objects.filter(
            due_date=reminder_date, status__in=["pending", "partially_paid"]
        ).select_related("student", "group", "course")

        for payment in upcoming_payments:
            if not dry_run:
                create_payment_notification(
                    title=f"Payment Due Soon: {payment.student.get_full_name()}",
                    message=f"Payment for {payment.student.get_full_name()} in {payment.group.name} "
                    f"is due on {payment.due_date}. "
                    f"Amount: ${payment.remaining_amount} (Period: {payment.payment_period})",
                    payment_type="tuition",
                    payment_status="pending",
                    amount=float(payment.remaining_amount),
                    currency="USD",
                    due_date=timezone.make_aware(
                        timezone.datetime.combine(
                            payment.due_date, timezone.datetime.min.time()
                        )
                    ),
                )
                notifications_sent += 1
            else:
                self.stdout.write(
                    f"Would send reminder for {payment.student.get_full_name()} "
                    f"(due {payment.due_date}, amount: ${payment.remaining_amount})"
                )
                notifications_sent += 1

        # Check overdue payments
        overdue_payments = Payment.objects.filter(
            due_date__lt=today, status__in=["pending", "partially_paid", "overdue"]
        ).select_related("student", "group", "course")

        for payment in overdue_payments:
            # Update status to overdue if not already
            if payment.status != "overdue":
                payment.status = "overdue"
                if not dry_run:
                    payment.save()

            if not dry_run:
                create_payment_notification(
                    title=f"OVERDUE PAYMENT: {payment.student.get_full_name()}",
                    message=f"Payment for {payment.student.get_full_name()} in {payment.group.name} "
                    f"is {payment.days_overdue} days overdue! "
                    f"Due date: {payment.due_date}. "
                    f"Amount: ${payment.remaining_amount} (Period: {payment.payment_period}). "
                    f"Please contact immediately!",
                    payment_type="tuition",
                    payment_status="overdue",
                    amount=float(payment.remaining_amount),
                    currency="USD",
                    due_date=timezone.make_aware(
                        timezone.datetime.combine(
                            payment.due_date, timezone.datetime.min.time()
                        )
                    ),
                )
                notifications_sent += 1
            else:
                self.stdout.write(
                    f"Would send overdue alert for {payment.student.get_full_name()} "
                    f"({payment.days_overdue} days overdue, amount: ${payment.remaining_amount})"
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
                    f"Successfully sent {notifications_sent} payment notifications"
                )
            )
