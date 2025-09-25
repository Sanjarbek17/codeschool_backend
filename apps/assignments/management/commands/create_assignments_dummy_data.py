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

        # Create tasks with proper programming problems
        self.stdout.write(f"Creating {tasks_count} programming tasks...")
        tasks_list = []

        # Define comprehensive programming problems with descriptions
        programming_problems = [
            {
                "title": "Factorial Calculator",
                "description": """Write a function named `factorial(n)` that calculates the factorial of a given non-negative integer n.

**Requirements:**
- The function should return 1 for n = 0
- Use either recursive or iterative approach
- Handle edge cases properly

**Example:**
```python
factorial(5)  # Returns: 120
factorial(0)  # Returns: 1
```""",
            },
            {
                "title": "Binary Search Implementation",
                "description": """Implement a binary search algorithm that finds the index of a target element in a sorted array.

**Requirements:**
- Function signature: `binary_search(arr, target)`
- Return the index if found, -1 if not found
- Array is guaranteed to be sorted in ascending order
- Use O(log n) time complexity

**Example:**
```python
binary_search([1, 2, 3, 4, 5], 3)  # Returns: 2
binary_search([1, 2, 3, 4, 5], 6)  # Returns: -1
```""",
            },
            {
                "title": "Two Sum Problem",
                "description": """Given an array of integers and a target sum, return the indices of two numbers that add up to the target.

**Requirements:**
- Function signature: `two_sum(nums, target)`
- Return a list containing two indices
- Each input has exactly one solution
- Cannot use the same element twice

**Example:**
```python
two_sum([2, 7, 11, 15], 9)  # Returns: [0, 1]
two_sum([3, 2, 4], 6)       # Returns: [1, 2]
```""",
            },
            {
                "title": "Prime Number Checker",
                "description": """Create a function that determines whether a given number is prime.

**Requirements:**
- Function signature: `is_prime(n)`
- Return True if prime, False otherwise
- Handle edge cases (n < 2)
- Optimize for efficiency

**Example:**
```python
is_prime(7)   # Returns: True
is_prime(4)   # Returns: False
is_prime(1)   # Returns: False
```""",
            },
            {
                "title": "Palindrome Checker",
                "description": """Write a function that checks if a string is a palindrome (reads the same forwards and backwards).

**Requirements:**
- Function signature: `is_palindrome(s)`
- Ignore case sensitivity
- Ignore spaces and punctuation
- Return boolean value

**Example:**
```python
is_palindrome("racecar")     # Returns: True
is_palindrome("A man a plan a canal Panama")  # Returns: True
```""",
            },
            {
                "title": "Fibonacci Sequence",
                "description": """Implement a function that returns the nth number in the Fibonacci sequence.

**Requirements:**
- Function signature: `fibonacci(n)`
- Use either recursive or iterative approach
- Handle edge cases (n < 0)
- 0th fibonacci number is 0, 1st is 1

**Example:**
```python
fibonacci(6)  # Returns: 8 (sequence: 0,1,1,2,3,5,8)
fibonacci(0)  # Returns: 0
```""",
            },
            {
                "title": "Array Sorting",
                "description": """Implement a sorting algorithm to sort an array of integers in ascending order.

**Requirements:**
- Function signature: `sort_array(arr)`
- Return a new sorted array
- Choose any sorting algorithm (bubble, insertion, merge, etc.)
- Handle empty arrays

**Example:**
```python
sort_array([64, 34, 25, 12, 22, 11, 90])  # Returns: [11, 12, 22, 25, 34, 64, 90]
sort_array([])  # Returns: []
```""",
            },
            {
                "title": "String Reversal",
                "description": """Create a function that reverses a given string.

**Requirements:**
- Function signature: `reverse_string(s)`
- Do not use built-in reverse functions
- Handle empty strings
- Preserve original string

**Example:**
```python
reverse_string("hello")  # Returns: "olleh"
reverse_string("")       # Returns: ""
```""",
            },
            {
                "title": "Maximum Element Finder",
                "description": """Write a function that finds the maximum element in a list of numbers.

**Requirements:**
- Function signature: `find_max(nums)`
- Handle empty lists appropriately
- Do not use built-in max() function
- Return None for empty list

**Example:**
```python
find_max([3, 7, 2, 9, 1])  # Returns: 9
find_max([])               # Returns: None
```""",
            },
            {
                "title": "Sum of Digits",
                "description": """Create a function that calculates the sum of all digits in a positive integer.

**Requirements:**
- Function signature: `sum_digits(n)`
- Handle single digit numbers
- Work with any positive integer
- Return 0 for n = 0

**Example:**
```python
sum_digits(123)   # Returns: 6 (1+2+3)
sum_digits(9)     # Returns: 9
```""",
            },
            {
                "title": "List Intersection",
                "description": """Find the common elements between two lists.

**Requirements:**
- Function signature: `find_intersection(list1, list2)`
- Return a list of common elements
- Remove duplicates from result
- Preserve order from first list

**Example:**
```python
find_intersection([1,2,3,4], [3,4,5,6])  # Returns: [3, 4]
find_intersection([1,2,3], [4,5,6])      # Returns: []
```""",
            },
            {
                "title": "Count Vowels",
                "description": """Write a function that counts the number of vowels in a given string.

**Requirements:**
- Function signature: `count_vowels(s)`
- Count both uppercase and lowercase vowels
- Vowels are: a, e, i, o, u
- Return integer count

**Example:**
```python
count_vowels("hello world")  # Returns: 3
count_vowels("Python")       # Returns: 1
```""",
            },
        ]

        # Generate tasks using the programming problems
        for i in range(tasks_count):
            homework = random.choice(homework_list)
            problem = random.choice(programming_problems)

            # Add variation to avoid exact duplicates
            task_number = (i % len(programming_problems)) + 1
            task_title = f"Problem {task_number}: {problem['title']}"

            task = Task.objects.create(
                homework=homework,
                title=task_title,
                description=problem["description"],
            )

            tasks_list.append(task)
            self.stdout.write(f"Created task: {task.title}")

        # Add extra tasks to some homework to ensure variety
        self.stdout.write(
            "Adding additional programming challenges to random homework..."
        )
        for homework in random.sample(homework_list, min(10, len(homework_list))):
            extra_tasks = random.randint(1, 3)
            for j in range(extra_tasks):
                problem = random.choice(programming_problems)
                task = Task.objects.create(
                    homework=homework,
                    title=f"Bonus Challenge: {problem['title']}",
                    description=problem["description"],
                )
                tasks_list.append(task)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(homework_list)} homework assignments and "
                f"{len(tasks_list)} tasks"
            )
        )
