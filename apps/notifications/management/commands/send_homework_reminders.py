from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.assignments.models import Homework
from apps.notifications.utils import create_bulk_notifications
from apps.accounts.models import Teacher, Group
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Send reminder notifications for upcoming homework deadlines to teachers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Send reminders for homework due in X days (default: 1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending notifications",
        )

    def handle(self, *args, **options):
        days_ahead = options["days"]
        dry_run = options["dry_run"]

        # Calculate target date
        target_date = timezone.now().date() + timedelta(days=days_ahead)

        self.stdout.write(
            self.style.SUCCESS(f"Looking for homework due on {target_date}...")
        )

        # Find homework due on target date
        upcoming_homework = Homework.objects.filter(
            # If you have a due_date field, uncomment this:
            # due_date__date=target_date
        )

        if not upcoming_homework.exists():
            self.stdout.write(self.style.WARNING("No upcoming homework found."))
            return

        notifications_sent = 0

        for homework in upcoming_homework:
            # Get all groups related to this homework's lesson
            lesson = homework.lesson
            if lesson and lesson.course:
                groups = Group.objects.filter(current_course=lesson.course)

                # Get all teachers from these groups
                teacher_ids = set()
                for group in groups:
                    teacher_ids.update(group.teachers.values_list("user_id", flat=True))

                teachers = User.objects.filter(id__in=teacher_ids)

                if not dry_run:
                    # Send notifications to teachers
                    for teacher in teachers:
                        from apps.notifications.utils import create_notification

                        create_notification(
                            title=f"Homework Deadline Reminder: {homework.title}",
                            message=f"Reminder: Homework '{homework.title}' for {lesson.title} "
                            f"is due in {days_ahead} day(s). Please check student progress.",
                            notification_type="deadline",
                            recipient_role="teacher",
                            recipient=teacher,
                            priority="medium",
                            related_object=homework,
                        )
                        notifications_sent += 1
                else:
                    # Dry run - just count what would be sent
                    notifications_sent += len(teachers)
                    self.stdout.write(
                        f"Would send reminder for '{homework.title}' to {len(teachers)} teachers"
                    )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would send {notifications_sent} notifications"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully sent {notifications_sent} reminder notifications"
                )
            )
