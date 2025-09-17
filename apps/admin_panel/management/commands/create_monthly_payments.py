from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from decimal import Decimal
from apps.admin_panel.models import Payment


class Command(BaseCommand):
    help = "Create monthly payment records for all active students"

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=int,
            help="Month for which to create payments (1-12). Defaults to current month.",
        )
        parser.add_argument(
            "--year",
            type=int,
            help="Year for which to create payments. Defaults to current year.",
        )
        parser.add_argument(
            "--amount",
            type=str,
            default="100.00",
            help="Default payment amount. Defaults to 100.00.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating payments.",
        )

    def handle(self, *args, **options):
        # Get current date info
        now = timezone.now()
        current_month = now.month
        current_year = now.year

        # Use provided values or defaults
        month = options["month"] or current_month
        year = options["year"] or current_year

        try:
            amount = Decimal(options["amount"])
        except (ValueError, TypeError):
            raise CommandError(f"Invalid amount: {options['amount']}")

        # Validate month
        if not (1 <= month <= 12):
            raise CommandError(f"Month must be between 1 and 12, got: {month}")

        # Validate year
        if year < 2020 or year > 2050:
            raise CommandError(f"Year must be between 2020 and 2050, got: {year}")

        self.stdout.write(
            self.style.SUCCESS(
                f"{'DRY RUN: ' if options['dry_run'] else ''}Creating payments for {month:02d}/{year} with amount {amount}"
            )
        )

        if options["dry_run"]:
            # Show what would be created
            from apps.accounts.models import Student

            students_with_groups = (
                Student.objects.filter(groups__isnull=False)
                .prefetch_related("groups")
                .distinct()
            )

            total_payments = 0
            for student in students_with_groups:
                for group in student.groups.all():
                    # Check if payment already exists
                    if not Payment.objects.filter(
                        student=student.user, group=group, month=month, year=year
                    ).exists():
                        total_payments += 1
                        self.stdout.write(
                            f"  Would create: {student.full_name} - {group.name} - {amount}"
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Already exists: {student.full_name} - {group.name}"
                            )
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN: Would create {total_payments} new payments"
                )
            )
            return

        # Actually create the payments
        try:
            created_payments = Payment.create_monthly_payments(month, year, amount)

            if created_payments:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully created {len(created_payments)} payments for {month:02d}/{year}"
                    )
                )

                # Show created payments
                for payment in created_payments:
                    self.stdout.write(
                        f"  Created: {payment.student.get_full_name()} - {payment.group.name} - {payment.amount}"
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"No new payments created for {month:02d}/{year}. "
                        "Payments may already exist or no active students found."
                    )
                )

        except Exception as e:
            raise CommandError(f"Error creating payments: {str(e)}")

        self.stdout.write(
            self.style.SUCCESS("Payment creation completed successfully!")
        )
