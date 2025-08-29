from django.core.management.base import BaseCommand
from apps.courses.models import Lessons, Attendance
from apps.accounts.models import Teacher, Student, Group
from faker import Faker
from datetime import date, timedelta
import random

fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for courses app models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--lessons", type=int, default=20, help="Number of lessons to create"
        )
        parser.add_argument(
            "--attendance-records",
            type=int,
            default=100,
            help="Number of attendance records to create",
        )

    def handle(self, *args, **options):
        lessons_count = options["lessons"]
        attendance_count = options["attendance_records"]

        self.stdout.write("Creating dummy data for courses app...")

        # Get existing teachers and students
        teachers = list(Teacher.objects.all())
        students = list(Student.objects.all())
        groups = list(Group.objects.all())

        if not teachers:
            self.stdout.write(
                self.style.WARNING(
                    "No teachers found. Run create_accounts_dummy_data first."
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

        if not groups:
            self.stdout.write(
                self.style.WARNING(
                    "No groups found. Run create_accounts_dummy_data first."
                )
            )
            return

        # Create lessons
        self.stdout.write(f"Creating {lessons_count} lessons...")
        lessons = []
        subjects = [
            "Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "Computer Science",
            "English",
            "History",
            "Geography",
            "Art",
            "Music",
        ]

        for i in range(lessons_count):
            subject = random.choice(subjects)
            lesson_number = random.randint(1, 50)

            lesson = Lessons.objects.create(
                title=f"{subject} - Lesson {lesson_number}: {fake.catch_phrase()}",
                description=fake.text(max_nb_chars=500),
                video_url=fake.url() if random.choice([True, False]) else None,
                content=fake.text(max_nb_chars=1000),
            )

            # Assign random teachers to lesson (1-2 teachers per lesson)
            selected_teachers = random.sample(
                teachers, min(random.randint(1, 2), len(teachers))
            )
            lesson.teachers.set(selected_teachers)

            lessons.append(lesson)
            self.stdout.write(f"Created lesson: {lesson.title}")

        # Create attendance records
        self.stdout.write(f"Creating {attendance_count} attendance records...")
        attendance_records = []
        statuses = ["present", "absent", "late", "excused"]

        for i in range(attendance_count):
            # Select random student, lesson, and group
            student = random.choice(students)
            lesson = random.choice(lessons)

            # Make sure the student belongs to at least one group
            student_groups = list(student.groups.all())
            if not student_groups:
                continue

            group = random.choice(student_groups)

            # Make sure at least one teacher from the lesson can teach this group
            lesson_teachers = list(lesson.teachers.all())
            group_teachers = list(group.teachers.all())
            common_teachers = list(set(lesson_teachers) & set(group_teachers))

            if not common_teachers:
                continue

            teacher = random.choice(common_teachers)

            # Generate random date within last 30 days
            random_date = fake.date_between(
                start_date=date.today() - timedelta(days=30), end_date=date.today()
            )

            # Check if attendance record already exists
            if not Attendance.objects.filter(
                student=student, lesson=lesson, group=group, date=random_date
            ).exists():
                attendance = Attendance.objects.create(
                    student=student,
                    lesson=lesson,
                    group=group,
                    teacher=teacher,
                    status=random.choice(statuses),
                    date=random_date,
                    notes=fake.sentence() if random.choice([True, False]) else "",
                )
                attendance_records.append(attendance)
                self.stdout.write(
                    f"Created attendance: {student.full_name} - {lesson.title} - {attendance.get_status_display()}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(lessons)} lessons and "
                f"{len(attendance_records)} attendance records"
            )
        )
