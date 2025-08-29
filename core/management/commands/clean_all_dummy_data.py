from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import User, Teacher, Student, Group
from apps.courses.models import Lessons, Attendance
from apps.assignments.models import Homework, Task
from apps.submissions.models import HomeworkSubmission, TestCase
from apps.progress.models import HomeworkProgress, TaskProgress


class Command(BaseCommand):
    help = "Clean all dummy data from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm that you want to delete all data",
        )
        parser.add_argument(
            "--keep-superusers", action="store_true", help="Keep superuser accounts"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "This command will delete ALL data from the database!\n"
                    "Use --confirm flag to proceed."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING("Cleaning all dummy data from database...")
        )

        try:
            # Count before deletion
            initial_counts = {
                "Users": User.objects.count(),
                "Teachers": Teacher.objects.count(),
                "Students": Student.objects.count(),
                "Groups": Group.objects.count(),
                "Lessons": Lessons.objects.count(),
                "Attendance": Attendance.objects.count(),
                "Homework": Homework.objects.count(),
                "Tasks": Task.objects.count(),
                "Submissions": HomeworkSubmission.objects.count(),
                "Test Cases": TestCase.objects.count(),
                "Homework Progress": HomeworkProgress.objects.count(),
                "Task Progress": TaskProgress.objects.count(),
            }

            # Delete in reverse dependency order
            self.stdout.write("Deleting progress records...")
            TaskProgress.objects.all().delete()
            HomeworkProgress.objects.all().delete()

            self.stdout.write("Deleting submissions...")
            HomeworkSubmission.objects.all().delete()
            TestCase.objects.all().delete()

            self.stdout.write("Deleting assignments...")
            Task.objects.all().delete()
            Homework.objects.all().delete()

            self.stdout.write("Deleting course data...")
            Attendance.objects.all().delete()
            Lessons.objects.all().delete()

            self.stdout.write("Deleting account data...")
            Group.objects.all().delete()
            Teacher.objects.all().delete()
            Student.objects.all().delete()

            # Delete users (keep superusers if requested)
            if options["keep_superusers"]:
                User.objects.filter(is_superuser=False).delete()
                self.stdout.write("Kept superuser accounts")
            else:
                User.objects.all().delete()
                self.stdout.write("Deleted all users including superusers")

            # Count after deletion
            final_counts = {
                "Users": User.objects.count(),
                "Teachers": Teacher.objects.count(),
                "Students": Student.objects.count(),
                "Groups": Group.objects.count(),
                "Lessons": Lessons.objects.count(),
                "Attendance": Attendance.objects.count(),
                "Homework": Homework.objects.count(),
                "Tasks": Task.objects.count(),
                "Submissions": HomeworkSubmission.objects.count(),
                "Test Cases": TestCase.objects.count(),
                "Homework Progress": HomeworkProgress.objects.count(),
                "Task Progress": TaskProgress.objects.count(),
            }

            # Print summary
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS("CLEANUP SUMMARY"))
            self.stdout.write("=" * 50)

            for model_name in initial_counts.keys():
                deleted_count = initial_counts[model_name] - final_counts[model_name]
                self.stdout.write(
                    f"{model_name}: {initial_counts[model_name]} → {final_counts[model_name]} "
                    f"({deleted_count} deleted)"
                )

            self.stdout.write("=" * 50)
            self.stdout.write(
                self.style.SUCCESS("✅ All dummy data has been successfully cleaned!")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error cleaning dummy data: {str(e)}"))
            raise
