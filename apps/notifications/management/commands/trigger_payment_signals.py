from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.signals import trigger_bulk_payment_check


class Command(BaseCommand):
    help = "Trigger signal-based payment notifications manually"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output",
        )

    def handle(self, *args, **options):
        verbose = options.get("verbose", False)

        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f"Starting manual payment check at {timezone.now()}")
            )

        try:
            notifications_sent = trigger_bulk_payment_check()

            self.stdout.write(
                self.style.SUCCESS(f"✅ Payment check completed successfully!")
            )
            self.stdout.write(
                self.style.SUCCESS(f"📧 Notifications sent: {notifications_sent}")
            )

            if verbose:
                self.stdout.write(self.style.SUCCESS(f"Completed at {timezone.now()}"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error during payment check: {str(e)}")
            )
            raise e
