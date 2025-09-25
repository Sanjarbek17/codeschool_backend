from django.core.management.base import BaseCommand
from apps.courses.models import Course
from apps.accounts.models import Teacher
from faker import Faker
import random

fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for Course models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--courses", type=int, default=15, help="Number of courses to create"
        )

    def handle(self, *args, **options):
        courses_count = options["courses"]

        self.stdout.write("Creating dummy data for Course models...")

        # Get existing teachers
        teachers = list(Teacher.objects.all())

        if not teachers:
            self.stdout.write(
                self.style.WARNING(
                    "No teachers found. Run create_accounts_dummy_data first."
                )
            )
            return

        # Course topics and levels
        course_topics = [
            "Python Programming",
            "Web Development",
            "Data Science",
            "Machine Learning",
            "JavaScript Fundamentals",
            "React Development",
            "Django Framework",
            "Database Design",
            "API Development",
            "Mobile App Development",
            "Game Development",
            "Cybersecurity",
            "DevOps Basics",
            "UI/UX Design",
            "Blockchain Development",
            "Cloud Computing",
            "Artificial Intelligence",
            "Software Testing",
            "System Administration",
            "Network Programming",
        ]

        levels = ["beginner", "intermediate", "advanced"]

        # Create courses
        self.stdout.write(f"Creating {courses_count} courses...")
        created_courses = []

        for i in range(courses_count):
            # Generate unique course title
            topic = random.choice(course_topics)
            level = random.choice(levels)

            # Ensure unique course titles
            title = f"{topic} - {level.title()}"
            counter = 1
            base_title = title
            while Course.objects.filter(title=title).exists():
                title = f"{base_title} {counter}"
                counter += 1

            course = Course.objects.create(
                title=title,
                description=fake.paragraph(nb_sentences=5),
                duration_weeks=random.randint(4, 20),
                level=level,
                is_active=random.choice([True, True, True, False]),  # 75% active
            )

            # Assign 1-3 teachers to each course
            assigned_teachers = random.sample(
                teachers, k=random.randint(1, min(3, len(teachers)))
            )
            course.teachers.set(assigned_teachers)

            created_courses.append(course)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {len(created_courses)} courses")
        )

        # Show sample of created courses
        for course in created_courses[:5]:
            self.stdout.write(
                f"  - {course.title} ({course.level}, {course.duration_weeks} weeks)"
            )
            self.stdout.write(f"    Teachers: {course.teacher_names}")

        if len(created_courses) > 5:
            self.stdout.write(f"  ... and {len(created_courses) - 5} more courses")
