"""
Django management command to create sample test cases.
Usage: python manage.py create_sample_tests
"""

from django.core.management.base import BaseCommand
from apps.submissions.models import TestCase
from apps.assignments.models import Task


class Command(BaseCommand):
    help = "Create sample test cases for demonstration"

    def handle(self, *args, **options):
        # Example test code for a simple function
        add_function_test = '''
import unittest

# Execute student's code safely
try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestAddNumbers(unittest.TestCase):
    
    def test_basic_addition(self):
        """Test basic addition functionality"""
        self.assertEqual(add_numbers(2, 3), 5)
        self.assertEqual(add_numbers(0, 0), 0)
        self.assertEqual(add_numbers(-1, 1), 0)
    
    def test_negative_numbers(self):
        """Test with negative numbers"""
        self.assertEqual(add_numbers(-5, -3), -8)
        self.assertEqual(add_numbers(-10, 5), -5)
    
    def test_large_numbers(self):
        """Test with large numbers"""
        self.assertEqual(add_numbers(1000000, 2000000), 3000000)

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
'''

        # Example test code for a class
        calculator_test = '''
import unittest

try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestCalculator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            self.calc = Calculator()
        except NameError:
            self.fail("Calculator class not found")
        except Exception as e:
            self.fail(f"Failed to create Calculator instance: {e}")
    
    def test_addition(self):
        """Test addition method"""
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-1, 1), 0)
    
    def test_subtraction(self):
        """Test subtraction method"""
        self.assertEqual(self.calc.subtract(5, 3), 2)
        self.assertEqual(self.calc.subtract(0, 5), -5)
    
    def test_multiplication(self):
        """Test multiplication method"""
        self.assertEqual(self.calc.multiply(3, 4), 12)
        self.assertEqual(self.calc.multiply(-2, 3), -6)
        self.assertEqual(self.calc.multiply(0, 5), 0)
    
    def test_division(self):
        """Test division method"""
        self.assertEqual(self.calc.divide(10, 2), 5)
        self.assertEqual(self.calc.divide(0, 5), 0)
    
    def test_division_by_zero(self):
        """Test division by zero handling"""
        with self.assertRaises(ZeroDivisionError):
            self.calc.divide(5, 0)

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
'''

        # Create test cases if tasks exist
        tasks = Task.objects.all()[:2]  # Get first 2 tasks for demonstration

        if not tasks:
            self.stdout.write(
                self.style.WARNING("No tasks found. Please create some tasks first.")
            )
            return

        created_count = 0

        for i, task in enumerate(tasks):
            if i == 0:
                # Create test case for add function
                test_case, created = TestCase.objects.get_or_create(
                    task=task,
                    test_code=add_function_test,
                    defaults={
                        "hidden": False,
                        "input_data": "Two numbers: a, b",
                        "expected_output": "Sum of a and b",
                        "timeout_seconds": 30,
                    },
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"Created test case for task: {task.title}")

            elif i == 1:
                # Create test case for calculator class
                test_case, created = TestCase.objects.get_or_create(
                    task=task,
                    test_code=calculator_test,
                    defaults={
                        "hidden": True,  # Hidden test case
                        "input_data": "Calculator operations",
                        "expected_output": "Correct arithmetic results",
                        "timeout_seconds": 45,
                    },
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        f"Created hidden test case for task: {task.title}"
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} test cases.")
        )
