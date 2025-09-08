# Test Code Implementation Guide

## Overview

The `test_code` field in the `TestCase` model should contain Python code that validates student submissions using the `unittest` framework. This document provides practical examples and guidelines for creating effective test cases.

## Key Components

### 1. Test Code Structure

Each test case should follow this basic structure:

```python
import unittest

# Execute student's code safely
try:
    exec(student_code)
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestStudentCode(unittest.TestCase):
    
    def test_something(self):
        # Your test logic here
        pass

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
```

### 2. Types of Tests

#### Function Testing
```python
def test_add_function(self):
    self.assertEqual(add_numbers(2, 3), 5)
    self.assertEqual(add_numbers(-1, 1), 0)
```

#### Class Testing
```python
def setUp(self):
    self.calc = Calculator()

def test_calculator_methods(self):
    self.assertEqual(self.calc.add(2, 3), 5)
```

#### Output Testing
```python
def test_program_output(self):
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        exec(student_code)
    self.assertEqual(captured_output.getvalue().strip(), "Hello, World!")
```

### 3. TestCase Model Fields

- **test_code**: The actual Python test code
- **input_data**: Description of test inputs (for documentation)
- **expected_output**: Description of expected results
- **timeout_seconds**: Maximum execution time (default: 30)
- **hidden**: Whether students can see this test case

### 4. Security Considerations

- **Execution limits**: Set memory and time constraints
- **Restricted imports**: Limit available modules
- **Safe execution environment**: Use subprocess isolation
- **Input validation**: Sanitize student code before execution

### 5. Best Practices

1. **Test edge cases**: Empty inputs, boundary values, error conditions
2. **Use descriptive names**: Clear test method names and docstrings
3. **Independent tests**: Each test should work regardless of others
4. **Proper cleanup**: Use setUp/tearDown for resource management
5. **Meaningful assertions**: Use appropriate unittest assertion methods

### 6. Common Test Patterns

#### Algorithm Validation
```python
def test_sorting_algorithm(self):
    test_cases = [
        ([3, 1, 4, 1, 5], [1, 1, 3, 4, 5]),
        ([], []),
        ([1], [1])
    ]
    for input_list, expected in test_cases:
        with self.subTest(input_list=input_list):
            self.assertEqual(sort_function(input_list.copy()), expected)
```

#### Error Handling
```python
def test_error_handling(self):
    with self.assertRaises(ValueError):
        invalid_function("bad_input")
```

#### Performance Testing
```python
def test_performance(self):
    import time
    start = time.time()
    result = expensive_function(large_input)
    execution_time = time.time() - start
    self.assertLess(execution_time, 1.0)  # Should complete in < 1 second
```

## Implementation Examples

See the following files for complete examples:
- `TEST_CODE_EXAMPLES.md` - Comprehensive examples
- `apps/submissions/test_examples.py` - Django integration examples
- `apps/submissions/management/commands/create_sample_tests.py` - Management command

## Integration with Submission System

The test execution flow:

1. **Student submits code** → `HomeworkSubmission` created
2. **System retrieves test cases** → `TestCase.objects.filter(task=submission.task)`
3. **Execute tests** → Run each test case against submission
4. **Update results** → Update `passed_tests` and `total_tests` fields
5. **Store metadata** → Save execution time, memory usage, etc.

## Example Usage in Views

```python
from apps.submissions.models import TestCase, HomeworkSubmission

def evaluate_submission(submission_id):
    submission = HomeworkSubmission.objects.get(id=submission_id)
    test_cases = TestCase.objects.filter(task=submission.task)
    
    passed_tests = 0
    total_tests = test_cases.count()
    
    for test_case in test_cases:
        success, message, exec_time = execute_test_case(test_case, submission)
        if success:
            passed_tests += 1
    
    submission.passed_tests = passed_tests
    submission.total_tests = total_tests
    submission.save()
    
    return submission.success_rate
```

This system provides a robust foundation for automated code evaluation in the educational platform.
