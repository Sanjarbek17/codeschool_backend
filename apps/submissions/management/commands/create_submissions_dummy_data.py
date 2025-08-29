from django.core.management.base import BaseCommand
from apps.submissions.models import HomeworkSubmission, TestCase
from apps.assignments.models import Task
from apps.accounts.models import Student
from faker import Faker
import random

fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for submissions app models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--submissions",
            type=int,
            default=200,
            help="Number of homework submissions to create",
        )
        parser.add_argument(
            "--test-cases", type=int, default=150, help="Number of test cases to create"
        )

    def handle(self, *args, **options):
        submissions_count = options["submissions"]
        test_cases_count = options["test_cases"]

        self.stdout.write("Creating dummy data for submissions app...")

        # Get existing tasks and students
        tasks = list(Task.objects.all())
        students = list(Student.objects.all())

        if not tasks:
            self.stdout.write(
                self.style.WARNING(
                    "No tasks found. Run create_assignments_dummy_data first."
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

        # Create test cases first
        self.stdout.write(f"Creating {test_cases_count} test cases...")
        test_cases_list = []

        # Sample code templates for different types of tasks
        python_test_templates = [
            "assert function_name(5) == 120  # Test factorial",
            "assert binary_search([1,2,3,4,5], 3) == 2  # Test binary search",
            "assert is_prime(7) == True  # Test prime check",
            "assert calculate_sum([1,2,3]) == 6  # Test sum function",
            "assert reverse_string('hello') == 'olleh'  # Test string reversal",
        ]

        math_test_templates = [
            "# Check if solution is correct for quadratic equation",
            "# Verify derivative calculation",
            "# Test integration result",
            "# Validate statistical calculation",
            "# Check probability distribution",
        ]

        for i in range(test_cases_count):
            task = random.choice(tasks)
            is_hidden = random.choice([True, False])

            # Choose appropriate test template based on task content
            if (
                "function" in task.description.lower()
                or "program" in task.description.lower()
            ):
                test_code = random.choice(python_test_templates)
                input_data = fake.pystr(max_chars=50)
                expected_output = fake.pystr(max_chars=100)
            else:
                test_code = random.choice(math_test_templates)
                input_data = fake.sentence()
                expected_output = fake.sentence()

            test_case = TestCase.objects.create(
                task=task,
                test_code=test_code,
                hidden=is_hidden,
                input_data=input_data,
                expected_output=expected_output,
                timeout_seconds=random.randint(5, 60),
            )

            test_cases_list.append(test_case)
            visibility = "Hidden" if is_hidden else "Visible"
            self.stdout.write(f"Created test case for {task.title} ({visibility})")

        # Create homework submissions
        self.stdout.write(f"Creating {submissions_count} homework submissions...")
        submissions_list = []

        # Sample code templates
        code_templates = [
            """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)""",
            """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1""",
            '''class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade
    
    def __str__(self):
        return f"{self.name}: {self.grade}"''',
            """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []""",
            """def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True""",
        ]

        for i in range(submissions_count):
            student = random.choice(students)
            task = random.choice(tasks)

            # Get test cases for this task to determine total_tests
            task_test_cases = TestCase.objects.filter(task=task)
            total_tests = task_test_cases.count()

            if total_tests == 0:
                total_tests = random.randint(3, 8)  # Default if no test cases

            passed_tests = random.randint(0, total_tests)

            # Choose appropriate code template
            code_text = random.choice(code_templates)

            # Add some variation to the code
            if random.choice([True, False]):
                code_text += f"\n\n# {fake.sentence()}"

            submission = HomeworkSubmission.objects.create(
                task=task,
                student=student,
                code_text=code_text,
                passed_tests=passed_tests,
                total_tests=total_tests,
                execution_time=random.uniform(0.1, 5.0),
                memory_usage=random.randint(1024, 8192),  # KB
            )

            submissions_list.append(submission)
            self.stdout.write(
                f"Created submission: {student.full_name} - {task.title} "
                f"({passed_tests}/{total_tests} tests passed)"
            )

        # Create additional submissions for some students to simulate multiple attempts
        self.stdout.write("Creating additional submissions for active students...")
        active_students = random.sample(students, min(20, len(students)))

        for student in active_students:
            additional_submissions = random.randint(1, 5)
            for j in range(additional_submissions):
                task = random.choice(tasks)

                # Check if student already has a submission for this task
                existing_submission = HomeworkSubmission.objects.filter(
                    student=student, task=task
                ).first()

                if existing_submission:
                    # Create improved submission
                    improved_passed = min(
                        existing_submission.total_tests,
                        existing_submission.passed_tests + random.randint(0, 2),
                    )
                else:
                    task_test_cases = TestCase.objects.filter(task=task)
                    total_tests = task_test_cases.count() or random.randint(3, 8)
                    improved_passed = random.randint(0, total_tests)

                submission = HomeworkSubmission.objects.create(
                    task=task,
                    student=student,
                    code_text=random.choice(code_templates)
                    + f"\n\n# Improved version {j+1}",
                    passed_tests=improved_passed,
                    total_tests=(
                        total_tests
                        if not existing_submission
                        else existing_submission.total_tests
                    ),
                    execution_time=random.uniform(0.1, 3.0),
                    memory_usage=random.randint(1024, 6144),
                )
                submissions_list.append(submission)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(test_cases_list)} test cases and "
                f"{len(submissions_list)} homework submissions"
            )
        )
