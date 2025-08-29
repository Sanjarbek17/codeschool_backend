from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.progress.models import HomeworkProgress, TaskProgress
from apps.assignments.models import Homework, Task
from apps.submissions.models import HomeworkSubmission
from apps.accounts.models import Student
from faker import Faker
from datetime import timedelta
import random

fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for progress app models"

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        homework_progress_count = options["homework_progress"]
        task_progress_count = options["task_progress"]

        self.stdout.write("Creating dummy data for progress app...")

        # Get existing data
        homework_list = list(Homework.objects.all())
        tasks = list(Task.objects.all())
        students = list(Student.objects.all())
        submissions = list(HomeworkSubmission.objects.all())

        if not homework_list:
            self.stdout.write(
                self.style.WARNING(
                    "No homework found. Run create_assignments_dummy_data first."
                )
            )
            return

        if not students:
            self.stdout.write(
                self.style.WARNING(
                    "No students found. Run create_accounts_dummy_data first."
                )
            )
            return

        if not tasks:
            self.stdout.write(
                self.style.WARNING(
                    "No tasks found. Run create_assignments_dummy_data first."
                )
            )
            return

        # Create homework progress records
        self.stdout.write(
            f"Creating {homework_progress_count} homework progress records..."
        )
        homework_progress_list = []

        for i in range(homework_progress_count):
            student = random.choice(students)
            homework = random.choice(homework_list)

            # Check if progress record already exists
            if HomeworkProgress.objects.filter(
                homework=homework, student=student
            ).exists():
                continue

            # Get actual number of tasks for this homework
            total_tasks = homework.tasks.count()
            if total_tasks == 0:
                total_tasks = random.randint(1, 10)  # Fallback if no tasks

            solved_tasks = random.randint(0, total_tasks)
            is_completed = solved_tasks >= total_tasks

            # Generate random last attempt time within last 7 days
            last_attempt = fake.date_time_between(
                start_date=timezone.now() - timedelta(days=7),
                end_date=timezone.now(),
                tzinfo=timezone.get_current_timezone(),
            )

            progress = HomeworkProgress.objects.create(
                homework=homework,
                student=student,
                total_tasks=total_tasks,
                solved_tasks=solved_tasks,
                is_completed=is_completed,
                last_attempt_at=last_attempt,
            )

            homework_progress_list.append(progress)
            completion_pct = (
                (solved_tasks / total_tasks * 100) if total_tasks > 0 else 0
            )
            self.stdout.write(
                f"Created homework progress: {student.full_name} - {homework.title} "
                f"({solved_tasks}/{total_tasks} tasks - {completion_pct:.1f}%)"
            )

        # Create task progress records
        self.stdout.write(f"Creating {task_progress_count} task progress records...")
        task_progress_list = []

        for i in range(task_progress_count):
            student = random.choice(students)
            task = random.choice(tasks)

            # Check if progress record already exists
            if TaskProgress.objects.filter(task=task, student=student).exists():
                continue

            # Get test cases count for this task or use random
            total_tests = task.test_cases.count()
            if total_tests == 0:
                total_tests = random.randint(3, 10)

            best_passed_tests = random.randint(0, total_tests)
            is_solved = best_passed_tests >= total_tests

            # Generate random last attempt time within last 14 days
            last_attempt = fake.date_time_between(
                start_date=timezone.now() - timedelta(days=14),
                end_date=timezone.now(),
                tzinfo=timezone.get_current_timezone(),
            )

            # Try to find a related submission
            last_submission = (
                HomeworkSubmission.objects.filter(task=task, student=student)
                .order_by("-submitted_at")
                .first()
            )

            progress = TaskProgress.objects.create(
                task=task,
                student=student,
                is_solved=is_solved,
                best_passed_tests=best_passed_tests,
                total_tests=total_tests,
                last_attempt_at=last_attempt,
                last_submission=last_submission,
            )

            task_progress_list.append(progress)
            pass_pct = (best_passed_tests / total_tests * 100) if total_tests > 0 else 0
            self.stdout.write(
                f"Created task progress: {student.full_name} - {task.title} "
                f"({best_passed_tests}/{total_tests} tests - {pass_pct:.1f}%)"
            )

        # Update some homework progress based on task progress
        self.stdout.write("Updating homework progress based on task progress...")
        for hw_progress in homework_progress_list:
            # Get all task progress for this homework and student
            homework_tasks = hw_progress.homework.tasks.all()
            completed_tasks = 0

            for task in homework_tasks:
                task_prog = TaskProgress.objects.filter(
                    task=task, student=hw_progress.student
                ).first()

                if task_prog and task_prog.is_solved:
                    completed_tasks += 1

            # Update homework progress if we have task progress data
            if homework_tasks.count() > 0:
                hw_progress.solved_tasks = completed_tasks
                hw_progress.is_completed = completed_tasks >= homework_tasks.count()
                hw_progress.save(update_fields=["solved_tasks", "is_completed"])

        # Create some additional progress records for active students
        self.stdout.write("Creating additional progress for active students...")
        active_students = random.sample(students, min(15, len(students)))

        for student in active_students:
            # Add more homework progress
            additional_hw = random.sample(homework_list, min(5, len(homework_list)))
            for homework in additional_hw:
                if not HomeworkProgress.objects.filter(
                    homework=homework, student=student
                ).exists():
                    total_tasks = homework.tasks.count() or random.randint(1, 8)
                    solved_tasks = random.randint(0, total_tasks)

                    HomeworkProgress.objects.create(
                        homework=homework,
                        student=student,
                        total_tasks=total_tasks,
                        solved_tasks=solved_tasks,
                        is_completed=solved_tasks >= total_tasks,
                        last_attempt_at=fake.date_time_between(
                            start_date=timezone.now() - timedelta(days=5),
                            end_date=timezone.now(),
                            tzinfo=timezone.get_current_timezone(),
                        ),
                    )

            # Add more task progress
            additional_tasks = random.sample(tasks, min(10, len(tasks)))
            for task in additional_tasks:
                if not TaskProgress.objects.filter(task=task, student=student).exists():
                    total_tests = task.test_cases.count() or random.randint(3, 8)
                    best_passed = random.randint(0, total_tests)

                    TaskProgress.objects.create(
                        task=task,
                        student=student,
                        is_solved=best_passed >= total_tests,
                        best_passed_tests=best_passed,
                        total_tests=total_tests,
                        last_attempt_at=fake.date_time_between(
                            start_date=timezone.now() - timedelta(days=3),
                            end_date=timezone.now(),
                            tzinfo=timezone.get_current_timezone(),
                        ),
                    )

        # Final count
        total_hw_progress = HomeworkProgress.objects.count()
        total_task_progress = TaskProgress.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created progress records:\n"
                f"- Homework Progress: {total_hw_progress} records\n"
                f"- Task Progress: {total_task_progress} records"
            )
        )
