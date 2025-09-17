from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.admin_panel.models import Payment, StudentPaymentStatus


class Command(BaseCommand):
    help = "Update payment status for all students and identify at-risk students"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without actually updating statuses.",
        )
        parser.add_argument(
            "--min-months",
            type=int,
            default=2,
            help="Minimum unpaid months to consider a student at risk (default: 2)",
        )
        parser.add_argument(
            "--suspension-months",
            type=int,
            default=3,
            help="Unpaid months required for suspension (default: 3)",
        )

    def handle(self, *args, **options):
        today = timezone.now().date()

        self.stdout.write(
            self.style.SUCCESS(
                f"{'DRY RUN: ' if options['dry_run'] else ''}Updating student payment statuses as of {today}"
            )
        )

        if options["dry_run"]:
            # Show what would be updated
            self.show_dry_run_preview(options)
        else:
            # Actually update statuses
            self.update_statuses(options)

    def show_dry_run_preview(self, options):
        """Show preview of what would be updated"""
        min_months = options["min_months"]
        suspension_months = options["suspension_months"]

        # Get students at risk
        students_at_risk = Payment.get_students_with_multiple_unpaid_months(min_months)
        suspension_candidates = Payment.get_suspension_candidates()

        self.stdout.write(
            self.style.WARNING(
                f"Students at risk ({min_months}+ unpaid months): {len(students_at_risk)}"
            )
        )

        for item in students_at_risk:
            student = item["student"]
            self.stdout.write(
                f"  {student.get_full_name()} - {item['unpaid_months']} months - "
                f"Debt: ${item['total_debt']}"
            )

        self.stdout.write(
            self.style.ERROR(
                f"Suspension candidates ({suspension_months}+ unpaid months): {len(suspension_candidates)}"
            )
        )

        for item in suspension_candidates:
            student = item["student"]
            self.stdout.write(
                f"  {student.get_full_name()} - {item['unpaid_months']} months - "
                f"Debt: ${item['total_debt']}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"DRY RUN: Would update payment statuses for these students"
            )
        )

    def update_statuses(self, options):
        """Actually update student payment statuses"""
        try:
            updated_count = StudentPaymentStatus.update_all_statuses()

            # Get current statistics
            status_counts = {}
            for status in ["active", "warning", "suspended", "expelled"]:
                count = StudentPaymentStatus.objects.filter(status=status).count()
                status_counts[status] = count

            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated payment status for {updated_count} students"
                )
            )

            self.stdout.write("Current status distribution:")
            for status, count in status_counts.items():
                color = self.style.SUCCESS
                if status == "warning":
                    color = self.style.WARNING
                elif status in ["suspended", "expelled"]:
                    color = self.style.ERROR

                self.stdout.write(f"  {color(status.title())}: {count}")

            # Show students needing attention
            warning_students = StudentPaymentStatus.objects.filter(status="warning")
            suspended_students = StudentPaymentStatus.objects.filter(status="suspended")

            if warning_students.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"\nStudents with payment warnings ({warning_students.count()}):"
                    )
                )
                for status in warning_students[:10]:  # Show first 10
                    self.stdout.write(
                        f"  {status.student.get_full_name()} - "
                        f"{status.consecutive_unpaid_months} months - "
                        f"${status.total_debt}"
                    )
                if warning_students.count() > 10:
                    self.stdout.write(f"  ... and {warning_students.count() - 10} more")

            if suspended_students.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"\nSuspended students ({suspended_students.count()}):"
                    )
                )
                for status in suspended_students:
                    self.stdout.write(
                        f"  {status.student.get_full_name()} - "
                        f"{status.consecutive_unpaid_months} months - "
                        f"${status.total_debt} - "
                        f"Suspended: {status.suspension_date}"
                    )

            # Check for new suspensions
            new_suspensions = StudentPaymentStatus.objects.filter(
                status="suspended", suspension_date=timezone.now().date()
            )

            if new_suspensions.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"\nNew suspensions today: {new_suspensions.count()}"
                    )
                )
                for status in new_suspensions:
                    self.stdout.write(f"  {status.student.get_full_name()}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error updating payment statuses: {str(e)}")
            )
            return

        self.stdout.write(
            self.style.SUCCESS("Payment status update completed successfully!")
        )
