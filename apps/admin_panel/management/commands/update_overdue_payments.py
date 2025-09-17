from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.admin_panel.models import Payment


class Command(BaseCommand):
    help = "Update pending payments that are past due date to overdue status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without actually updating payments.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed information about updated payments.",
        )

    def handle(self, *args, **options):
        today = timezone.now().date()

        self.stdout.write(
            self.style.SUCCESS(
                f"{'DRY RUN: ' if options['dry_run'] else ''}Checking for overdue payments as of {today}"
            )
        )

        # Find pending and partially paid payments that are past due
        overdue_payments = Payment.objects.filter(
            status__in=["pending", "partially_paid"], due_date__lt=today
        ).select_related("student", "group")

        if not overdue_payments.exists():
            self.stdout.write(self.style.SUCCESS("No overdue payments found!"))
            return

        if options["dry_run"]:
            # Show what would be updated
            self.stdout.write(
                self.style.WARNING(
                    f"Found {overdue_payments.count()} payments to mark as overdue:"
                )
            )

            for payment in overdue_payments:
                days_overdue = (today - payment.due_date).days
                self.stdout.write(
                    f"  {payment.student.get_full_name()} - {payment.group.name} - "
                    f"Due: {payment.due_date} ({days_overdue} days overdue) - Amount: {payment.amount}"
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN: Would update {overdue_payments.count()} payments to overdue status"
                )
            )
            return

        # Actually update the payments
        updated_payments = []

        for payment in overdue_payments:
            old_status = payment.status
            payment.status = "overdue"
            payment.save()
            updated_payments.append(payment)

            if options["verbose"]:
                days_overdue = (today - payment.due_date).days
                self.stdout.write(
                    f"  Updated: {payment.student.get_full_name()} - {payment.group.name} - "
                    f"Due: {payment.due_date} ({days_overdue} days overdue) - "
                    f"Status: {old_status} → overdue"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {len(updated_payments)} payments to overdue status!"
            )
        )

        # Show summary by group
        if options["verbose"] and updated_payments:
            from collections import defaultdict

            group_summary = defaultdict(int)
            for payment in updated_payments:
                group_summary[payment.group.name] += 1

            self.stdout.write("\nSummary by group:")
            for group_name, count in group_summary.items():
                self.stdout.write(f"  {group_name}: {count} overdue payments")

        self.stdout.write(
            self.style.SUCCESS("Overdue payment update completed successfully!")
        )
