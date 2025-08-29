from django.core.management.base import BaseCommand
from apps.assignments.models import Homework, Task
from apps.courses.models import Lessons
from faker import Faker
import random

fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for assignments app models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--homework",
            type=int,
            default=30,
            help="Number of homework assignments to create",
        )
        parser.add_argument(
            "--tasks", type=int, default=100, help="Number of tasks to create"
        )

    def handle(self, *args, **options):
        homework_count = options["homework"]
        tasks_count = options["tasks"]

        self.stdout.write("Creating dummy data for assignments app...")

        # Get existing lessons
        lessons = list(Lessons.objects.all())

        if not lessons:
            self.stdout.write(
                self.style.WARNING(
                    "No lessons found. Run create_courses_dummy_data first."
                )
            )
            return

        # Create homework assignments
        self.stdout.write(f"Creating {homework_count} homework assignments...")
        homework_list = []
        homework_types = [
            "Practice Problems",
            "Review Questions",
            "Lab Assignment",
            "Project Work",
            "Research Task",
            "Quiz Preparation",
            "Reading Assignment",
            "Problem Set",
            "Case Study",
            "Essay",
        ]

        for i in range(homework_count):
            lesson = random.choice(lessons)
            homework_type = random.choice(homework_types)

            homework = Homework.objects.create(
                lesson=lesson,
                title=f"{homework_type}: {fake.catch_phrase()}",
                description=fake.text(max_nb_chars=500),
            )

            homework_list.append(homework)
            self.stdout.write(f"Created homework: {homework.title}")

        # Create tasks
        self.stdout.write(f"Creating {tasks_count} tasks...")
        tasks_list = []
        programming_tasks = [
            "Write a function to calculate factorial",
            "Implement binary search algorithm",
            "Create a class for managing student records",
            "Solve the two-sum problem",
            "Implement a basic calculator",
            "Write a program to find prime numbers",
            "Create a simple text parser",
            "Implement sorting algorithms",
            "Build a basic data structure",
            "Write unit tests for given code",
        ]

        math_tasks = [
            "Solve quadratic equations",
            "Calculate derivatives",
            "Find the area under a curve",
            "Solve system of linear equations",
            "Calculate probability distributions",
            "Prove geometric theorems",
            "Analyze statistical data",
            "Optimize functions",
            "Calculate matrix operations",
            "Solve differential equations",
        ]

        general_tasks = [
            "Analyze the given text passage",
            "Summarize the chapter content",
            "Compare and contrast concepts",
            "Identify key themes",
            "Explain the process step by step",
            "Provide examples and counterexamples",
            "Critique the given argument",
            "Design an experiment",
            "Create a presentation",
            "Write a research report",
        ]

        all_task_templates = programming_tasks + math_tasks + general_tasks

        for i in range(tasks_count):
            homework = random.choice(homework_list)
            task_template = random.choice(all_task_templates)

            # Add some variation to the task title
            task_title = f"Task {i+1}: {task_template}"
            if random.choice([True, False]):
                task_title += f" - {fake.word().capitalize()}"

            task = Task.objects.create(
                homework=homework,
                title=task_title,
                description=fake.text(max_nb_chars=800),
            )

            tasks_list.append(task)
            self.stdout.write(f"Created task: {task.title}")

        # Add extra tasks to some homework to ensure variety
        self.stdout.write("Adding additional tasks to random homework...")
        for homework in random.sample(homework_list, min(10, len(homework_list))):
            extra_tasks = random.randint(1, 3)
            for j in range(extra_tasks):
                task_template = random.choice(all_task_templates)
                task = Task.objects.create(
                    homework=homework,
                    title=f"Bonus Task: {task_template}",
                    description=fake.text(max_nb_chars=600),
                )
                tasks_list.append(task)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(homework_list)} homework assignments and "
                f"{len(tasks_list)} tasks"
            )
        )
