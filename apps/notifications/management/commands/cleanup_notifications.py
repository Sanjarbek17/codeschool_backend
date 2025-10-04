from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = "Clean up old read notifications to keep the database optimized"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete read notifications older than X days (default: 30)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--keep-payment",
            action="store_true",
            help="Keep payment notifications even if they are old",
        )

    def handle(self, *args, **options):
        days_old = options["days"]
        dry_run = options["dry_run"]
        keep_payment = options["keep_payment"]

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days_old)

        self.stdout.write(
            self.style.SUCCESS(
                f"Looking for read notifications older than {cutoff_date.date()}..."
            )
        )

        # Base query - read notifications older than cutoff
        old_notifications = Notification.objects.filter(
            is_read=True, read_at__lt=cutoff_date
        )

        # Optionally exclude payment notifications
        if keep_payment:
            old_notifications = old_notifications.exclude(
                notification_type__in=["payment", "student_payment", "teacher_payment"]
            )

        count = old_notifications.count()

        if count == 0:
            self.stdout.write(
                self.style.WARNING("No old notifications found to clean up.")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would delete {count} old notifications")
            )

            # Show breakdown by type
            breakdown = (
                old_notifications.values("notification_type")
                .annotate(count=Count("id"))
                .order_by("notification_type")
            )

            for item in breakdown:
                self.stdout.write(f"  {item['notification_type']}: {item['count']}")
        else:
            # Actually delete the notifications
            deleted_count, _ = old_notifications.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {deleted_count} old notifications"
                )
            )
