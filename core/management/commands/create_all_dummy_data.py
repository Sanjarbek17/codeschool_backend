from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = "Create dummy data for all apps in the correct order"

    def add_arguments(self, parser):
        parser.add_argument(
            "--teachers", type=int, default=10, help="Number of teachers to create"
        )
        parser.add_argument(
            "--students", type=int, default=50, help="Number of students to create"
        )
        parser.add_argument(
            "--groups", type=int, default=5, help="Number of groups to create"
        )
        parser.add_argument(
            "--lessons", type=int, default=20, help="Number of lessons to create"
        )
        parser.add_argument(
            "--attendance-records",
            type=int,
            default=100,
            help="Number of attendance records to create",
        )
        parser.add_argument(
            "--homework",
            type=int,
            default=30,
            help="Number of homework assignments to create",
        )
        parser.add_argument(
            "--tasks", type=int, default=100, help="Number of tasks to create"
        )
        parser.add_argument(
            "--submissions",
            type=int,
            default=200,
            help="Number of homework submissions to create",
        )
        parser.add_argument(
            "--test-cases", type=int, default=150, help="Number of test cases to create"
        )
        parser.add_argument(
            "--homework-progress",
            type=int,
            default=100,
            help="Number of homework progress records to create",
        )
        parser.add_argument(
            "--task-progress",
            type=int,
            default=300,
            help="Number of task progress records to create",
        )
        parser.add_argument(
            "--skip-accounts",
            action="store_true",
            help="Skip creating accounts dummy data",
        )
        parser.add_argument(
            "--skip-courses",
            action="store_true",
            help="Skip creating courses dummy data",
        )
        parser.add_argument(
            "--skip-assignments",
            action="store_true",
            help="Skip creating assignments dummy data",
        )
        parser.add_argument(
            "--skip-submissions",
            action="store_true",
            help="Skip creating submissions dummy data",
        )
        parser.add_argument(
            "--skip-progress",
            action="store_true",
            help="Skip creating progress dummy data",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Starting comprehensive dummy data creation...")
        )

        try:
            # Step 1: Create accounts (users, teachers, students, groups)
            if not options["skip_accounts"]:
                self.stdout.write(
                    self.style.HTTP_INFO("Step 1: Creating accounts dummy data...")
                )
                call_command(
                    "create_accounts_dummy_data",
                    teachers=options["teachers"],
                    students=options["students"],
                    groups=options["groups"],
                    verbosity=1,
                )
            else:
                self.stdout.write("Skipping accounts dummy data creation")

            # Step 2: Create courses (lessons and attendance)
            if not options["skip_courses"]:
                self.stdout.write(
                    self.style.HTTP_INFO("Step 2: Creating courses dummy data...")
                )
                call_command(
                    "create_courses_dummy_data",
                    lessons=options["lessons"],
                    attendance_records=options["attendance_records"],
                    verbosity=1,
                )
            else:
                self.stdout.write("Skipping courses dummy data creation")

            # Step 3: Create assignments (homework and tasks)
            if not options["skip_assignments"]:
                self.stdout.write(
                    self.style.HTTP_INFO("Step 3: Creating assignments dummy data...")
                )
                call_command(
                    "create_assignments_dummy_data",
                    homework=options["homework"],
                    tasks=options["tasks"],
                    verbosity=1,
                )
            else:
                self.stdout.write("Skipping assignments dummy data creation")

            # Step 4: Create submissions (homework submissions and test cases)
            if not options["skip_submissions"]:
                self.stdout.write(
                    self.style.HTTP_INFO("Step 4: Creating submissions dummy data...")
                )
                call_command(
                    "create_submissions_dummy_data",
                    submissions=options["submissions"],
                    test_cases=options["test_cases"],
                    verbosity=1,
                )
            else:
                self.stdout.write("Skipping submissions dummy data creation")

            # Step 5: Create progress (homework and task progress)
            if not options["skip_progress"]:
                self.stdout.write(
                    self.style.HTTP_INFO("Step 5: Creating progress dummy data...")
                )
                call_command(
                    "create_progress_dummy_data",
                    homework_progress=options["homework_progress"],
                    task_progress=options["task_progress"],
                    verbosity=1,
                )
            else:
                self.stdout.write("Skipping progress dummy data creation")

            self.stdout.write(
                self.style.SUCCESS(
                    "\n🎉 Successfully created all dummy data!\n"
                    "You can now use the following commands to create specific data:\n"
                    "- python manage.py create_accounts_dummy_data\n"
                    "- python manage.py create_courses_dummy_data\n"
                    "- python manage.py create_assignments_dummy_data\n"
                    "- python manage.py create_submissions_dummy_data\n"
                    "- python manage.py create_progress_dummy_data\n"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating dummy data: {str(e)}"))
            raise

    def print_summary(self):
        """Print a summary of created data"""
        from apps.accounts.models import User, Teacher, Student, Group
        from apps.courses.models import Lessons, Attendance
        from apps.assignments.models import Homework, Task
        from apps.submissions.models import HomeworkSubmission, TestCase
        from apps.progress.models import HomeworkProgress, TaskProgress

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("DUMMY DATA SUMMARY"))
        self.stdout.write("=" * 50)

        # Accounts
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Teachers: {Teacher.objects.count()}")
        self.stdout.write(f"Students: {Student.objects.count()}")
        self.stdout.write(f"Groups: {Group.objects.count()}")

        # Courses
        self.stdout.write(f"Lessons: {Lessons.objects.count()}")
        self.stdout.write(f"Attendance Records: {Attendance.objects.count()}")

        # Assignments
        self.stdout.write(f"Homework: {Homework.objects.count()}")
        self.stdout.write(f"Tasks: {Task.objects.count()}")

        # Submissions
        self.stdout.write(f"Homework Submissions: {HomeworkSubmission.objects.count()}")
        self.stdout.write(f"Test Cases: {TestCase.objects.count()}")

        # Progress
        self.stdout.write(f"Homework Progress: {HomeworkProgress.objects.count()}")
        self.stdout.write(f"Task Progress: {TaskProgress.objects.count()}")

        self.stdout.write("=" * 50)
