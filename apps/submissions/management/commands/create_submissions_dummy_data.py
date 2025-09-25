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

        # Define test cases for specific programming problems
        test_case_mappings = {
            "Factorial Calculator": [
                {
                    "test_code": "assert factorial(5) == 120",
                    "input_data": "5",
                    "expected_output": "120",
                    "hidden": False,
                },
                {
                    "test_code": "assert factorial(0) == 1",
                    "input_data": "0",
                    "expected_output": "1",
                    "hidden": False,
                },
                {
                    "test_code": "assert factorial(1) == 1",
                    "input_data": "1",
                    "expected_output": "1",
                    "hidden": True,
                },
                {
                    "test_code": "assert factorial(10) == 3628800",
                    "input_data": "10",
                    "expected_output": "3628800",
                    "hidden": True,
                },
            ],
            "Binary Search Implementation": [
                {
                    "test_code": "assert binary_search([1,2,3,4,5], 3) == 2",
                    "input_data": "[1,2,3,4,5], 3",
                    "expected_output": "2",
                    "hidden": False,
                },
                {
                    "test_code": "assert binary_search([1,2,3,4,5], 6) == -1",
                    "input_data": "[1,2,3,4,5], 6",
                    "expected_output": "-1",
                    "hidden": False,
                },
                {
                    "test_code": "assert binary_search([1], 1) == 0",
                    "input_data": "[1], 1",
                    "expected_output": "0",
                    "hidden": True,
                },
                {
                    "test_code": "assert binary_search([], 1) == -1",
                    "input_data": "[], 1",
                    "expected_output": "-1",
                    "hidden": True,
                },
            ],
            "Two Sum Problem": [
                {
                    "test_code": "assert two_sum([2,7,11,15], 9) == [0,1]",
                    "input_data": "[2,7,11,15], 9",
                    "expected_output": "[0,1]",
                    "hidden": False,
                },
                {
                    "test_code": "assert two_sum([3,2,4], 6) == [1,2]",
                    "input_data": "[3,2,4], 6",
                    "expected_output": "[1,2]",
                    "hidden": False,
                },
                {
                    "test_code": "assert two_sum([3,3], 6) == [0,1]",
                    "input_data": "[3,3], 6",
                    "expected_output": "[0,1]",
                    "hidden": True,
                },
            ],
            "Prime Number Checker": [
                {
                    "test_code": "assert is_prime(7) == True",
                    "input_data": "7",
                    "expected_output": "True",
                    "hidden": False,
                },
                {
                    "test_code": "assert is_prime(4) == False",
                    "input_data": "4",
                    "expected_output": "False",
                    "hidden": False,
                },
                {
                    "test_code": "assert is_prime(1) == False",
                    "input_data": "1",
                    "expected_output": "False",
                    "hidden": True,
                },
                {
                    "test_code": "assert is_prime(29) == True",
                    "input_data": "29",
                    "expected_output": "True",
                    "hidden": True,
                },
            ],
            "Palindrome Checker": [
                {
                    "test_code": "assert is_palindrome('racecar') == True",
                    "input_data": "racecar",
                    "expected_output": "True",
                    "hidden": False,
                },
                {
                    "test_code": "assert is_palindrome('hello') == False",
                    "input_data": "hello",
                    "expected_output": "False",
                    "hidden": False,
                },
                {
                    "test_code": "assert is_palindrome('A man a plan a canal Panama') == True",
                    "input_data": "A man a plan a canal Panama",
                    "expected_output": "True",
                    "hidden": True,
                },
            ],
            "Fibonacci Sequence": [
                {
                    "test_code": "assert fibonacci(6) == 8",
                    "input_data": "6",
                    "expected_output": "8",
                    "hidden": False,
                },
                {
                    "test_code": "assert fibonacci(0) == 0",
                    "input_data": "0",
                    "expected_output": "0",
                    "hidden": False,
                },
                {
                    "test_code": "assert fibonacci(10) == 55",
                    "input_data": "10",
                    "expected_output": "55",
                    "hidden": True,
                },
            ],
            "Array Sorting": [
                {
                    "test_code": "assert sort_array([64,34,25,12,22,11,90]) == [11,12,22,25,34,64,90]",
                    "input_data": "[64,34,25,12,22,11,90]",
                    "expected_output": "[11,12,22,25,34,64,90]",
                    "hidden": False,
                },
                {
                    "test_code": "assert sort_array([]) == []",
                    "input_data": "[]",
                    "expected_output": "[]",
                    "hidden": False,
                },
                {
                    "test_code": "assert sort_array([1]) == [1]",
                    "input_data": "[1]",
                    "expected_output": "[1]",
                    "hidden": True,
                },
            ],
            "String Reversal": [
                {
                    "test_code": "assert reverse_string('hello') == 'olleh'",
                    "input_data": "hello",
                    "expected_output": "olleh",
                    "hidden": False,
                },
                {
                    "test_code": "assert reverse_string('') == ''",
                    "input_data": "",
                    "expected_output": "",
                    "hidden": False,
                },
                {
                    "test_code": "assert reverse_string('Python') == 'nohtyP'",
                    "input_data": "Python",
                    "expected_output": "nohtyP",
                    "hidden": True,
                },
            ],
            "Maximum Element Finder": [
                {
                    "test_code": "assert find_max([3,7,2,9,1]) == 9",
                    "input_data": "[3,7,2,9,1]",
                    "expected_output": "9",
                    "hidden": False,
                },
                {
                    "test_code": "assert find_max([]) == None",
                    "input_data": "[]",
                    "expected_output": "None",
                    "hidden": False,
                },
                {
                    "test_code": "assert find_max([-1,-5,-3]) == -1",
                    "input_data": "[-1,-5,-3]",
                    "expected_output": "-1",
                    "hidden": True,
                },
            ],
            "Sum of Digits": [
                {
                    "test_code": "assert sum_digits(123) == 6",
                    "input_data": "123",
                    "expected_output": "6",
                    "hidden": False,
                },
                {
                    "test_code": "assert sum_digits(9) == 9",
                    "input_data": "9",
                    "expected_output": "9",
                    "hidden": False,
                },
                {
                    "test_code": "assert sum_digits(0) == 0",
                    "input_data": "0",
                    "expected_output": "0",
                    "hidden": True,
                },
            ],
            "List Intersection": [
                {
                    "test_code": "assert find_intersection([1,2,3,4], [3,4,5,6]) == [3,4]",
                    "input_data": "[1,2,3,4], [3,4,5,6]",
                    "expected_output": "[3,4]",
                    "hidden": False,
                },
                {
                    "test_code": "assert find_intersection([1,2,3], [4,5,6]) == []",
                    "input_data": "[1,2,3], [4,5,6]",
                    "expected_output": "[]",
                    "hidden": False,
                },
            ],
            "Count Vowels": [
                {
                    "test_code": "assert count_vowels('hello world') == 3",
                    "input_data": "hello world",
                    "expected_output": "3",
                    "hidden": False,
                },
                {
                    "test_code": "assert count_vowels('Python') == 1",
                    "input_data": "Python",
                    "expected_output": "1",
                    "hidden": False,
                },
                {
                    "test_code": "assert count_vowels('') == 0",
                    "input_data": "",
                    "expected_output": "0",
                    "hidden": True,
                },
            ],
        }

        # Create test cases for each task
        tasks_processed = 0
        for task in tasks:
            # Find matching test cases based on task title
            matching_tests = None
            for problem_name, tests in test_case_mappings.items():
                if problem_name in task.title:
                    matching_tests = tests
                    break

            if matching_tests:
                # Create all test cases for this specific problem
                for test_data in matching_tests:
                    test_case = TestCase.objects.create(
                        task=task,
                        test_code=test_data["test_code"],
                        hidden=test_data["hidden"],
                        input_data=test_data["input_data"],
                        expected_output=test_data["expected_output"],
                        timeout_seconds=30,
                    )
                    test_cases_list.append(test_case)
                    visibility = "Hidden" if test_data["hidden"] else "Visible"
                    self.stdout.write(
                        f"Created test case for {task.title} ({visibility})"
                    )

                tasks_processed += 1
                if tasks_processed >= test_cases_count:
                    break
            else:
                # Create generic test cases for tasks that don't match our mappings
                for i in range(3):  # Create 3 test cases per unmatched task
                    test_case = TestCase.objects.create(
                        task=task,
                        test_code="# Generic test case - implement based on requirements",
                        hidden=i > 1,  # First 2 visible, rest hidden
                        input_data="sample_input",
                        expected_output="sample_output",
                        timeout_seconds=30,
                    )
                    test_cases_list.append(test_case)
                    visibility = "Hidden" if i > 1 else "Visible"
                    self.stdout.write(
                        f"Created generic test case for {task.title} ({visibility})"
                    )

                    tasks_processed += 1
                    if tasks_processed >= test_cases_count:
                        break

            if tasks_processed >= test_cases_count:
                break

        # Create homework submissions
        self.stdout.write(f"Creating {submissions_count} homework submissions...")
        submissions_list = []

        # Code solutions for different programming problems
        code_solutions = {
            "Factorial Calculator": [
                # Correct solution
                """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)""",
                # Alternative iterative solution
                """def factorial(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result""",
                # Partially correct (missing edge case)
                """def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)""",
            ],
            "Binary Search Implementation": [
                # Correct solution
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
                # Recursive solution
                """def binary_search(arr, target):
    def search(left, right):
        if left > right:
            return -1
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            return search(mid + 1, right)
        else:
            return search(left, mid - 1)
    return search(0, len(arr) - 1)""",
            ],
            "Two Sum Problem": [
                # Optimal hash map solution
                """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []""",
                # Brute force solution
                """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []""",
            ],
            "Prime Number Checker": [
                # Optimized solution
                """def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True""",
                # Simple solution
                """def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True""",
            ],
            "Palindrome Checker": [
                # Clean solution
                """def is_palindrome(s):
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]""",
                # Alternative solution
                """def is_palindrome(s):
    s = s.lower().replace(' ', '')
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True""",
            ],
            "Fibonacci Sequence": [
                # Iterative solution
                """def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b""",
                # Recursive solution
                """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)""",
            ],
            "Array Sorting": [
                # Bubble sort
                """def sort_array(arr):
    if not arr:
        return []
    result = arr.copy()
    n = len(result)
    for i in range(n):
        for j in range(0, n-i-1):
            if result[j] > result[j+1]:
                result[j], result[j+1] = result[j+1], result[j]
    return result""",
                # Using built-in sort
                """def sort_array(arr):
    return sorted(arr)""",
            ],
            "String Reversal": [
                # Manual reversal
                """def reverse_string(s):
    result = ""
    for char in s:
        result = char + result
    return result""",
                # Using slicing
                """def reverse_string(s):
    return s[::-1]""",
            ],
            "Maximum Element Finder": [
                # Manual search
                """def find_max(nums):
    if not nums:
        return None
    max_val = nums[0]
    for num in nums[1:]:
        if num > max_val:
            max_val = num
    return max_val""",
            ],
            "Sum of Digits": [
                # String approach
                """def sum_digits(n):
    return sum(int(digit) for digit in str(n))""",
                # Mathematical approach
                """def sum_digits(n):
    total = 0
    while n > 0:
        total += n % 10
        n //= 10
    return total""",
            ],
            "List Intersection": [
                # Using sets
                """def find_intersection(list1, list2):
    set2 = set(list2)
    result = []
    for item in list1:
        if item in set2 and item not in result:
            result.append(item)
    return result""",
            ],
            "Count Vowels": [
                # Simple approach
                """def count_vowels(s):
    vowels = 'aeiouAEIOU'
    return sum(1 for char in s if char in vowels)""",
            ],
        }

        for i in range(submissions_count):
            student = random.choice(students)
            task = random.choice(tasks)

            # Get test cases for this task to determine total_tests
            task_test_cases = TestCase.objects.filter(task=task)
            total_tests = task_test_cases.count()

            if total_tests == 0:
                total_tests = random.randint(3, 8)  # Default if no test cases

            # Find matching code solution based on task title
            code_text = "# TODO: Implement solution"
            for problem_name, solutions in code_solutions.items():
                if problem_name in task.title:
                    code_text = random.choice(solutions)
                    break

            # Determine passed tests based on code quality
            if "TODO" in code_text:
                passed_tests = random.randint(
                    0, total_tests // 2
                )  # Poor performance for incomplete code
            elif "# Simple" in code_text or "brute force" in code_text.lower():
                passed_tests = random.randint(
                    total_tests // 2, total_tests
                )  # Decent performance
            else:
                passed_tests = random.randint(
                    max(0, total_tests - 2), total_tests
                )  # Good performance

            # Add some variation to the code
            if random.choice([True, False]) and "TODO" not in code_text:
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

                # Find appropriate code solution for improved submission
                improved_code = "# TODO: Implement improved solution"
                for problem_name, solutions in code_solutions.items():
                    if problem_name in task.title:
                        improved_code = random.choice(solutions)
                        break

                submission = HomeworkSubmission.objects.create(
                    task=task,
                    student=student,
                    code_text=improved_code + f"\n\n# Improved version {j+1}",
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
