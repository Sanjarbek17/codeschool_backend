#!/usr/bin/env python3
"""
Python script to run payment reminder commands on schedule
Using the schedule library for easy scheduling
"""

import os
import sys
import django
import schedule
import time
import logging
from datetime import datetime
from django.core.management import call_command

# Setup Django
project_root = "/Volumes/Transcend/backend/codeschool_backend"
sys.path.append(project_root)
os.chdir(project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# Setup logging
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "payment_scheduler.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def run_payment_reminders():
    """Run the payment reminder command"""
    try:
        logger.info("Starting payment reminder check...")

        # Run the management command
        call_command("check_payment_dues", days_ahead=3, verbosity=1)

        logger.info("Payment reminder check completed successfully")

    except Exception as e:
        logger.error(f"Error running payment reminders: {str(e)}")


def run_weekly_cleanup():
    """Run weekly notification cleanup"""
    try:
        logger.info("Starting weekly notification cleanup...")

        # Run cleanup command (keep notifications for 30 days)
        call_command("cleanup_notifications", days=30, keep_payment=True, verbosity=1)

        logger.info("Weekly cleanup completed successfully")

    except Exception as e:
        logger.error(f"Error running weekly cleanup: {str(e)}")


def main():
    """Main scheduler function"""
    logger.info("Payment Reminder Scheduler Starting...")

    # Schedule daily payment reminders at 9:00 AM
    schedule.every().day.at("09:00").do(run_payment_reminders)

    # Schedule weekly cleanup on Sundays at 2:00 AM
    schedule.every().sunday.at("02:00").do(run_weekly_cleanup)

    # Optional: Run homework reminders on weekdays at 8:00 AM
    schedule.every().monday.at("08:00").do(
        lambda: call_command("send_homework_reminders", days=1, verbosity=1)
    )
    schedule.every().tuesday.at("08:00").do(
        lambda: call_command("send_homework_reminders", days=1, verbosity=1)
    )
    schedule.every().wednesday.at("08:00").do(
        lambda: call_command("send_homework_reminders", days=1, verbosity=1)
    )
    schedule.every().thursday.at("08:00").do(
        lambda: call_command("send_homework_reminders", days=1, verbosity=1)
    )
    schedule.every().friday.at("08:00").do(
        lambda: call_command("send_homework_reminders", days=1, verbosity=1)
    )

    logger.info("Scheduled jobs:")
    logger.info("- Daily payment reminders: 9:00 AM")
    logger.info("- Weekly cleanup: Sunday 2:00 AM")
    logger.info("- Homework reminders: Weekdays 8:00 AM")
    logger.info("Scheduler is running... Press Ctrl+C to stop")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")


if __name__ == "__main__":
    main()
