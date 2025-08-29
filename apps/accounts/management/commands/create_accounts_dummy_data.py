from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Teacher, Student, Group
from faker import Faker
import random

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for accounts app models"

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

    def handle(self, *args, **options):
        teachers_count = options["teachers"]
        students_count = options["students"]
        groups_count = options["groups"]

        self.stdout.write("Creating dummy data for accounts app...")

        # Create users and teachers
        self.stdout.write(f"Creating {teachers_count} teachers...")
        teachers = []
        for i in range(teachers_count):
            # Create user for teacher
            username = f"teacher_{i+1}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=fake.email(),
                    password="password123",
                    is_staff=True,
                )

                # Create teacher profile
                teacher = Teacher.objects.create(
                    user=user,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone_number=fake.phone_number(),
                )
                teachers.append(teacher)
                self.stdout.write(f"Created teacher: {teacher.full_name}")

        # Create groups
        self.stdout.write(f"Creating {groups_count} groups...")
        groups = []
        for i in range(groups_count):
            group_name = f"Group {fake.word().capitalize()}-{i+1}"
            if not Group.objects.filter(name=group_name).exists():
                group = Group.objects.create(name=group_name)

                # Assign random teachers to group (1-3 teachers per group)
                if teachers:
                    selected_teachers = random.sample(
                        teachers, min(random.randint(1, 3), len(teachers))
                    )
                    group.teachers.set(selected_teachers)

                groups.append(group)
                self.stdout.write(f"Created group: {group.name}")

        # Create users and students
        self.stdout.write(f"Creating {students_count} students...")
        students = []
        for i in range(students_count):
            # Create user for student
            username = f"student_{i+1}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username, email=fake.email(), password="password123"
                )

                # Create student profile
                student = Student.objects.create(
                    user=user,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone_number=fake.phone_number(),
                    parents_phone_number=fake.phone_number(),
                )

                # Assign student to random groups (1-2 groups per student)
                if groups:
                    selected_groups = random.sample(
                        groups, min(random.randint(1, 2), len(groups))
                    )
                    student.groups.set(selected_groups)

                students.append(student)
                self.stdout.write(f"Created student: {student.full_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(teachers)} teachers, "
                f"{len(students)} students, and {len(groups)} groups"
            )
        )
