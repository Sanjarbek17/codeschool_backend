"""
Example test case creation for the submissions app.
This file demonstrates how to create TestCase instances with proper test code.
"""

from apps.submissions.models import TestCase
from apps.assignments.models import Task, Homework
from apps.courses.models import Lessons


def create_sample_test_cases():
    """
    Create sample test cases for different types of programming tasks.
    This function demonstrates how to properly structure test code for the TestCase model.
    """

    # Example 1: Simple function testing
    simple_function_test = """
import unittest

# Execute student's code safely
try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestAddNumbers(unittest.TestCase):
    
    def test_positive_numbers(self):
        self.assertEqual(add_numbers(2, 3), 5)
        self.assertEqual(add_numbers(10, 15), 25)
    
    def test_negative_numbers(self):
        self.assertEqual(add_numbers(-2, -3), -5)
        self.assertEqual(add_numbers(-10, 5), -5)
    
    def test_zero(self):
        self.assertEqual(add_numbers(0, 0), 0)
        self.assertEqual(add_numbers(5, 0), 5)

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
"""

    # Example 2: Class method testing
    class_test = """
import unittest

try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestCalculator(unittest.TestCase):
    
    def setUp(self):
        try:
            self.calc = Calculator()
        except NameError:
            self.fail("Calculator class not found")
    
    def test_addition(self):
        self.assertEqual(self.calc.add(2, 3), 5)
    
    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            self.calc.divide(5, 0)

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
"""

    # Example 3: Output testing
    output_test = """
import unittest
import sys
import io
from contextlib import redirect_stdout

class TestOutput(unittest.TestCase):
    
    def test_hello_world(self):
        captured_output = io.StringIO()
        try:
            with redirect_stdout(captured_output):
                exec(student_code)
            output = captured_output.getvalue().strip()
            self.assertEqual(output, "Hello, World!")
        except Exception as e:
            self.fail(f"Code execution failed: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
"""

    # Example 4: Algorithm testing with edge cases
    algorithm_test = """
import unittest

try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestIsPrime(unittest.TestCase):
    
    def test_prime_numbers(self):
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        for num in primes:
            with self.subTest(num=num):
                self.assertTrue(is_prime(num), f"{num} should be prime")
    
    def test_non_prime_numbers(self):
        non_primes = [1, 4, 6, 8, 9, 10, 12, 14, 15]
        for num in non_primes:
            with self.subTest(num=num):
                self.assertFalse(is_prime(num), f"{num} should not be prime")
    
    def test_edge_cases(self):
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(1))
        self.assertTrue(is_prime(2))

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
"""

    # Store test code examples in a dictionary for easy access
    test_examples = {
        "simple_function": {
            "code": simple_function_test,
            "input_data": "a=2, b=3",
            "expected_output": "5",
            "description": "Test for add_numbers function",
        },
        "class_methods": {
            "code": class_test,
            "input_data": "Calculator instance operations",
            "expected_output": "Correct arithmetic results",
            "description": "Test for Calculator class methods",
        },
        "output_testing": {
            "code": output_test,
            "input_data": "No input required",
            "expected_output": "Hello, World!",
            "description": "Test for console output",
        },
        "algorithm_testing": {
            "code": algorithm_test,
            "input_data": "Various numbers",
            "expected_output": "True/False for prime check",
            "description": "Test for is_prime algorithm",
        },
    }

    return test_examples


def create_test_case_for_task(task, test_type="simple_function", hidden=False):
    """
    Create a TestCase instance for a given task.

    Args:
        task: Task model instance
        test_type: Type of test from the examples above
        hidden: Whether the test case should be hidden from students

    Returns:
        TestCase: Created test case instance
    """
    test_examples = create_sample_test_cases()

    if test_type not in test_examples:
        raise ValueError(
            f"Invalid test_type. Choose from: {list(test_examples.keys())}"
        )

    example = test_examples[test_type]

    test_case = TestCase.objects.create(
        task=task,
        test_code=example["code"],
        hidden=hidden,
        input_data=example["input_data"],
        expected_output=example["expected_output"],
        timeout_seconds=30,
    )

    return test_case


# Example usage in Django management command or view
def example_usage():
    """
    Example of how to use these test cases in practice.
    This would typically be called from a management command or admin interface.
    """

    # Get or create a task (assuming you have the related models)
    # homework = Homework.objects.first()
    # task = Task.objects.filter(homework=homework).first()

    # Create different types of test cases for the task
    # test_case_1 = create_test_case_for_task(task, 'simple_function', hidden=False)
    # test_case_2 = create_test_case_for_task(task, 'algorithm_testing', hidden=True)

    # The test cases are now ready to be used for validating student submissions
    pass


# Security considerations for test execution
SECURE_TEST_TEMPLATE = """
import unittest
import sys
import resource
import signal
import tempfile
import os

# Security wrapper
class SecureTestExecution:
    def __init__(self, timeout=30, memory_limit=100*1024*1024):
        self.timeout = timeout
        self.memory_limit = memory_limit
    
    def execute_with_limits(self, test_code, student_code):
        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
        
        # Set timeout
        def timeout_handler(signum, frame):
            raise TimeoutError("Test execution timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout)
        
        try:
            # Execute in restricted environment
            restricted_globals = {
                'student_code': student_code,
                '__builtins__': {
                    'len': len, 'str': str, 'int': int, 'float': float,
                    'list': list, 'dict': dict, 'tuple': tuple,
                    'range': range, 'enumerate': enumerate,
                    'print': print, 'isinstance': isinstance,
                    'Exception': Exception, 'ValueError': ValueError,
                    'TypeError': TypeError, 'IndexError': IndexError,
                    'KeyError': KeyError, 'ZeroDivisionError': ZeroDivisionError,
                }
            }
            
            exec(test_code, restricted_globals)
            return True, "Tests passed"
            
        except Exception as e:
            return False, str(e)
        finally:
            signal.alarm(0)  # Cancel timeout

# Your test code goes here...
{test_code}
"""

# Security execution class
import time
import resource
import signal


class SecureTestExecution:
    def __init__(self, timeout=30, memory_limit=100 * 1024 * 1024):
        self.timeout = timeout
        self.memory_limit = memory_limit

    def execute_with_limits(self, test_code, student_code):
        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))

        # Set timeout
        def timeout_handler(signum, frame):
            raise TimeoutError("Test execution timed out")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout)

        try:
            # Execute in restricted environment
            restricted_globals = {
                "student_code": student_code,
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "range": range,
                    "enumerate": enumerate,
                    "print": print,
                    "isinstance": isinstance,
                    "Exception": Exception,
                    "ValueError": ValueError,
                    "TypeError": TypeError,
                    "IndexError": IndexError,
                    "KeyError": KeyError,
                    "ZeroDivisionError": ZeroDivisionError,
                },
            }

            exec(test_code, restricted_globals)
            return True, "Tests passed"

        except Exception as e:
            return False, str(e)
        finally:
            signal.alarm(0)  # Cancel timeout


# Example of how to integrate with Django model
def execute_test_case(test_case_instance, student_submission):
    """
    Execute a TestCase against a student submission.

    Args:
        test_case_instance: TestCase model instance
        student_submission: HomeworkSubmission model instance

    Returns:
        tuple: (success: bool, message: str, execution_time: float)
    """
    start_time = time.time()

    try:
        # Get the test code and student code
        test_code = test_case_instance.test_code
        student_code = student_submission.code_text

        # Create secure execution environment
        executor = SecureTestExecution(
            timeout=test_case_instance.timeout_seconds,
            memory_limit=100 * 1024 * 1024,  # 100MB
        )

        # Execute the test
        success, message = executor.execute_with_limits(test_code, student_code)

        execution_time = time.time() - start_time

        return success, message, execution_time

    except Exception as e:
        execution_time = time.time() - start_time
        return False, f"Test execution error: {str(e)}", execution_time
