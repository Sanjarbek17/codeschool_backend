from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Sum, Q
from apps.admin_panel.models import Payment
from apps.accounts.models import Student, Group


class Command(BaseCommand):
    help = "Generate payment reports and statistics"

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=int,
            help="Month for report (1-12). Defaults to current month.",
        )
        parser.add_argument(
            "--year",
            type=int,
            help="Year for report. Defaults to current year.",
        )
        parser.add_argument(
            "--group",
            type=str,
            help="Generate report for specific group name.",
        )
        parser.add_argument(
            "--overdue-only",
            action="store_true",
            help="Show only overdue payments.",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            help="Show only summary statistics.",
        )

    def handle(self, *args, **options):
        # Get current date info
        now = timezone.now()
        current_month = now.month
        current_year = now.year

        # Use provided values or defaults
        month = options["month"] or current_month
        year = options["year"] or current_year

        self.stdout.write(self.style.SUCCESS(f"Payment Report for {month:02d}/{year}"))
        self.stdout.write("=" * 50)

        # Base queryset
        payments = Payment.objects.filter(month=month, year=year)

        # Apply filters
        if options["group"]:
            try:
                group = Group.objects.get(name__icontains=options["group"])
                payments = payments.filter(group=group)
                self.stdout.write(f"Filtered by group: {group.name}")
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Group not found: {options['group']}")
                )
                return

        if options["overdue_only"]:
            today = timezone.now().date()
            payments = payments.filter(
                status__in=["pending", "overdue"], due_date__lt=today
            )
            self.stdout.write("Showing overdue payments only")

        # Get statistics
        stats = payments.aggregate(
            total_count=Count("id"),
            total_amount=Sum("amount"),
            paid_count=Count("id", filter=Q(status="paid")),
            pending_count=Count("id", filter=Q(status="pending")),
            overdue_count=Count("id", filter=Q(status="overdue")),
            cancelled_count=Count("id", filter=Q(status="cancelled")),
            paid_amount=Sum("amount", filter=Q(status="paid")),
        )

        # Calculate derived statistics
        stats["outstanding_amount"] = (stats["total_amount"] or 0) - (
            stats["paid_amount"] or 0
        )
        stats["payment_rate"] = (
            (stats["paid_count"] / stats["total_count"] * 100)
            if stats["total_count"] > 0
            else 0
        )

        # Display summary
        self.stdout.write("\nSUMMARY STATISTICS:")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Total Payments: {stats['total_count']}")
        self.stdout.write(f"Total Amount: ${stats['total_amount'] or 0:.2f}")
        self.stdout.write(f"Payment Rate: {stats['payment_rate']:.1f}%")
        self.stdout.write("")
        self.stdout.write("Payment Status Breakdown:")
        self.stdout.write(
            f"  Paid: {stats['paid_count']} (${stats['paid_amount'] or 0:.2f})"
        )
        self.stdout.write(f"  Pending: {stats['pending_count']}")
        self.stdout.write(f"  Overdue: {stats['overdue_count']}")
        self.stdout.write(f"  Cancelled: {stats['cancelled_count']}")
        self.stdout.write(f"Outstanding Amount: ${stats['outstanding_amount']:.2f}")

        if options["summary_only"]:
            return

        # Group-wise breakdown
        self.stdout.write("\nGROUP-WISE BREAKDOWN:")
        self.stdout.write("-" * 30)

        group_stats = (
            payments.values("group__name")
            .annotate(
                total_count=Count("id"),
                total_amount=Sum("amount"),
                paid_count=Count("id", filter=Q(status="paid")),
                pending_count=Count("id", filter=Q(status="pending")),
                overdue_count=Count("id", filter=Q(status="overdue")),
                paid_amount=Sum("amount", filter=Q(status="paid")),
            )
            .order_by("group__name")
        )

        for group_stat in group_stats:
            group_name = group_stat["group__name"]
            outstanding = (group_stat["total_amount"] or 0) - (
                group_stat["paid_amount"] or 0
            )
            payment_rate = (
                (group_stat["paid_count"] / group_stat["total_count"] * 100)
                if group_stat["total_count"] > 0
                else 0
            )

            self.stdout.write(f"\n{group_name}:")
            self.stdout.write(
                f"  Total: {group_stat['total_count']} payments (${group_stat['total_amount'] or 0:.2f})"
            )
            self.stdout.write(
                f"  Paid: {group_stat['paid_count']} (${group_stat['paid_amount'] or 0:.2f})"
            )
            self.stdout.write(f"  Pending: {group_stat['pending_count']}")
            self.stdout.write(f"  Overdue: {group_stat['overdue_count']}")
            self.stdout.write(f"  Outstanding: ${outstanding:.2f}")
            self.stdout.write(f"  Payment Rate: {payment_rate:.1f}%")

        # Show individual overdue payments if any
        if not options["overdue_only"]:
            today = timezone.now().date()
            overdue_payments = (
                payments.filter(status__in=["pending", "overdue"], due_date__lt=today)
                .select_related("student", "group")
                .order_by("due_date")
            )

            if overdue_payments.exists():
                self.stdout.write("\nOVERDUE PAYMENTS:")
                self.stdout.write("-" * 30)

                for payment in overdue_payments:
                    days_overdue = (today - payment.due_date).days
                    self.stdout.write(
                        f"{payment.student.get_full_name()} - {payment.group.name} - "
                        f"${payment.amount} - Due: {payment.due_date} ({days_overdue} days overdue)"
                    )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Report completed successfully!")
