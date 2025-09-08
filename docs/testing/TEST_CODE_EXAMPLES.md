# Test Code Examples for TestCase Model

This document provides examples of how the `test_code` field in the `TestCase` model should be structured for different types of programming tasks.

## Overview

The `test_code` field contains Python code that will be executed to validate student submissions. The test code should:

1. **Import necessary modules** for testing
2. **Define test functions** that validate specific aspects of the student's code
3. **Use assertions** to check expected behavior
4. **Handle edge cases** and error conditions
5. **Be secure** and prevent malicious code execution

## Basic Structure

```python
# Basic test structure
import unittest
import sys
import io
from contextlib import redirect_stdout

# Import the student's submitted code
# Note: The student's code will be available as a module
exec(student_code)  # This will be replaced with secure execution

class TestSubmission(unittest.TestCase):
    
    def test_functionality(self):
        # Test cases here
        pass

if __name__ == '__main__':
    unittest.main()
```

## Example 1: Simple Function Testing

**Task**: Write a function `add_numbers(a, b)` that returns the sum of two numbers.

```python
import unittest

# Execute student's code safely
try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestAddNumbers(unittest.TestCase):
    
    def test_positive_numbers(self):
        """Test with positive numbers"""
        self.assertEqual(add_numbers(2, 3), 5)
        self.assertEqual(add_numbers(10, 15), 25)
    
    def test_negative_numbers(self):
        """Test with negative numbers"""
        self.assertEqual(add_numbers(-2, -3), -5)
        self.assertEqual(add_numbers(-10, 5), -5)
    
    def test_zero(self):
        """Test with zero"""
        self.assertEqual(add_numbers(0, 0), 0)
        self.assertEqual(add_numbers(5, 0), 5)
    
    def test_float_numbers(self):
        """Test with floating point numbers"""
        self.assertAlmostEqual(add_numbers(2.5, 3.7), 6.2, places=1)

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
```

## Example 2: Class Testing

**Task**: Create a `Calculator` class with methods for basic arithmetic operations.

```python
import unittest

# Execute student's code
try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestCalculator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
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
    
    def test_division(self):
        """Test division method"""
        self.assertEqual(self.calc.divide(10, 2), 5)
        self.assertAlmostEqual(self.calc.divide(7, 3), 2.333, places=3)
    
    def test_division_by_zero(self):
        """Test division by zero error handling"""
        with self.assertRaises(ZeroDivisionError):
            self.calc.divide(5, 0)

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
```

## Example 3: Output Testing

**Task**: Write a program that prints "Hello, World!" to the console.

```python
import unittest
import sys
import io
from contextlib import redirect_stdout

class TestHelloWorld(unittest.TestCase):
    
    def test_hello_world_output(self):
        """Test if the program outputs 'Hello, World!'"""
        # Capture stdout
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
```

## Example 4: Algorithm Testing with Multiple Test Cases

**Task**: Implement a function `is_prime(n)` that checks if a number is prime.

```python
import unittest

# Execute student's code
try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestIsPrime(unittest.TestCase):
    
    def test_prime_numbers(self):
        """Test with known prime numbers"""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
        for num in primes:
            with self.subTest(num=num):
                self.assertTrue(is_prime(num), f"{num} should be prime")
    
    def test_non_prime_numbers(self):
        """Test with non-prime numbers"""
        non_primes = [1, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20]
        for num in non_primes:
            with self.subTest(num=num):
                self.assertFalse(is_prime(num), f"{num} should not be prime")
    
    def test_edge_cases(self):
        """Test edge cases"""
        self.assertFalse(is_prime(0), "0 should not be prime")
        self.assertFalse(is_prime(1), "1 should not be prime")
        self.assertTrue(is_prime(2), "2 should be prime")
    
    def test_negative_numbers(self):
        """Test with negative numbers"""
        self.assertFalse(is_prime(-5), "Negative numbers should not be prime")
        self.assertFalse(is_prime(-2), "Negative numbers should not be prime")

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
```

## Example 5: Data Structure Testing

**Task**: Implement a `Stack` class with push, pop, and is_empty methods.

```python
import unittest

# Execute student's code
try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestStack(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            self.stack = Stack()
        except NameError:
            self.fail("Stack class not found")
        except Exception as e:
            self.fail(f"Failed to create Stack instance: {e}")
    
    def test_new_stack_is_empty(self):
        """Test that a new stack is empty"""
        self.assertTrue(self.stack.is_empty())
    
    def test_push_single_item(self):
        """Test pushing a single item"""
        self.stack.push(1)
        self.assertFalse(self.stack.is_empty())
    
    def test_push_multiple_items(self):
        """Test pushing multiple items"""
        items = [1, 2, 3, 4, 5]
        for item in items:
            self.stack.push(item)
        self.assertFalse(self.stack.is_empty())
    
    def test_pop_single_item(self):
        """Test popping a single item"""
        self.stack.push(42)
        popped = self.stack.pop()
        self.assertEqual(popped, 42)
        self.assertTrue(self.stack.is_empty())
    
    def test_pop_lifo_order(self):
        """Test that items are popped in LIFO order"""
        items = [1, 2, 3, 4, 5]
        for item in items:
            self.stack.push(item)
        
        for expected in reversed(items):
            with self.subTest(expected=expected):
                self.assertEqual(self.stack.pop(), expected)
    
    def test_pop_empty_stack(self):
        """Test popping from an empty stack"""
        with self.assertRaises(IndexError):
            self.stack.pop()

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
```

## Example 6: File I/O Testing

**Task**: Write a function `count_lines(filename)` that counts lines in a text file.

```python
import unittest
import tempfile
import os

# Execute student's code
try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestCountLines(unittest.TestCase):
    
    def setUp(self):
        """Create temporary test files"""
        # Create a temporary file with known content
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        test_content = "Line 1\nLine 2\nLine 3\nLine 4\n"
        self.temp_file.write(test_content)
        self.temp_file.close()
        
        # Create an empty file
        self.empty_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.empty_file.close()
    
    def tearDown(self):
        """Clean up temporary files"""
        os.unlink(self.temp_file.name)
        os.unlink(self.empty_file.name)
    
    def test_count_lines_normal_file(self):
        """Test counting lines in a normal file"""
        result = count_lines(self.temp_file.name)
        self.assertEqual(result, 4)
    
    def test_count_lines_empty_file(self):
        """Test counting lines in an empty file"""
        result = count_lines(self.empty_file.name)
        self.assertEqual(result, 0)
    
    def test_nonexistent_file(self):
        """Test with non-existent file"""
        with self.assertRaises(FileNotFoundError):
            count_lines("nonexistent_file.txt")

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
```

## Security Considerations

When writing test code, always consider security:

```python
import unittest
import sys
import resource
import signal

# Security wrapper for test execution
class SecureTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up security constraints"""
        # Limit memory usage (100MB)
        resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))
        
        # Set up timeout handler
        def timeout_handler(signum, frame):
            raise TimeoutError("Test execution timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
    
    def tearDown(self):
        """Clean up security constraints"""
        signal.alarm(0)  # Cancel timeout
```

## Best Practices

1. **Use descriptive test method names** that explain what is being tested
2. **Include docstrings** for test methods to explain the purpose
3. **Test edge cases** including empty inputs, boundary values, and error conditions
4. **Use `subTest`** for testing multiple similar cases
5. **Set up proper test fixtures** in `setUp()` method
6. **Clean up resources** in `tearDown()` method
7. **Handle exceptions gracefully** and provide meaningful error messages
8. **Use appropriate assertion methods** (`assertEqual`, `assertTrue`, `assertRaises`, etc.)
9. **Keep tests independent** - each test should work regardless of others
10. **Consider performance** - set timeouts and memory limits for resource-intensive tasks

## Integration with Django TestCase Model

The test code examples above can be stored in the `test_code` field of the `TestCase` model. The execution framework should:

1. **Safely execute** the student's code in a sandboxed environment
2. **Run the test code** against the student's submission
3. **Capture results** and update the `HomeworkSubmission` model
4. **Handle timeouts** and resource limits
5. **Log execution details** for debugging and monitoring

```python
# Example of how the test execution might work in practice
def execute_test_case(test_case, student_code):
    """
    Execute a test case against student code.
    
    Args:
        test_case: TestCase model instance
        student_code: String containing student's code
    
    Returns:
        dict: Test results including pass/fail status and details
    """
    try:
        # Create a secure execution environment
        test_globals = {
            'student_code': student_code,
            '__builtins__': __builtins__,
        }
        
        # Execute the test code
        exec(test_case.test_code, test_globals)
        
        return {
            'passed': True,
            'message': 'All tests passed',
            'execution_time': 0.5,  # seconds
            'memory_usage': 1024,   # KB
        }
        
    except Exception as e:
        return {
            'passed': False,
            'message': str(e),
            'execution_time': None,
            'memory_usage': None,
        }
```
