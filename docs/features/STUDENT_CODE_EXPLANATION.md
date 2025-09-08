# How `student_code` Works - Complete Explanation

## The Flow of Test Execution

The `student_code` variable in your test cases is **NOT** something you need to define in the admin panel. It's automatically provided by the test execution system when evaluating student submissions.

## Step-by-Step Process:

### 1. Student Submits Code
When a student submits their homework, it gets stored in the `HomeworkSubmission` model:

```python
# Student submits this code through the frontend
student_submission = """
def add_numbers(a, b):
    return a + b
"""

# This gets saved to HomeworkSubmission.code_text field
submission = HomeworkSubmission.objects.create(
    task=some_task,
    student=some_student,
    code_text=student_submission,  # <-- This is the student's code
    # ... other fields
)
```

### 2. System Retrieves Test Cases
The system finds all test cases for that task:

```python
# Get all test cases for this task
test_cases = TestCase.objects.filter(task=submission.task)
```

### 3. Test Execution Engine Runs Tests
When executing tests, the system does something like this:

```python
def execute_test_case(test_case, homework_submission):
    # Get the student's submitted code
    student_code = homework_submission.code_text
    
    # Get the test code from the TestCase model
    test_code = test_case.test_code
    
    # Create execution environment with student_code available
    test_globals = {
        'student_code': student_code,  # <-- This is where student_code comes from!
        '__builtins__': safe_builtins,
    }
    
    # Execute the test code
    exec(test_code, test_globals)
```

## Visual Flow Diagram:

```
Student Frontend
     ↓
[Student types: def add_numbers(a,b): return a+b]
     ↓
HomeworkSubmission.code_text = "def add_numbers(a,b): return a+b"
     ↓
Test Execution System
     ↓
student_code = submission.code_text  # Gets the student's code
     ↓
TestCase.test_code (your admin test) + student_code = Test Execution
     ↓
Results stored back to HomeworkSubmission (passed_tests, total_tests)
```

## What Happens During Test Execution:

### Before Execution:
```python
# In TestCase.test_code field (what you put in admin):
import unittest

try:
    exec(student_code)  # student_code is undefined here
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")
```

### During Execution:
```python
# The system provides student_code automatically:
student_code = "def add_numbers(a, b):\n    return a + b"

# Now when exec(student_code) runs, it defines the add_numbers function
exec(student_code)  # This creates the add_numbers function in the test environment

# Now your tests can call add_numbers(2, 3) and it will work
```

## Complete Example Implementation:

Here's how you might implement the test execution system:

```python
# In your views.py or services.py
def evaluate_submission(submission_id):
    """
    Evaluate a student submission against all test cases.
    """
    # Get the submission
    submission = HomeworkSubmission.objects.get(id=submission_id)
    
    # Get all test cases for this task
    test_cases = TestCase.objects.filter(task=submission.task)
    
    passed_tests = 0
    total_tests = test_cases.count()
    
    for test_case in test_cases:
        try:
            # Execute the test case against student code
            success = run_test_case(test_case, submission)
            if success:
                passed_tests += 1
                
        except Exception as e:
            # Test failed due to error
            print(f"Test failed: {e}")
    
    # Update submission with results
    submission.passed_tests = passed_tests
    submission.total_tests = total_tests
    submission.save()
    
    return submission


def run_test_case(test_case, submission):
    """
    Run a single test case against a submission.
    """
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    
    # Get the student's code
    student_code = submission.code_text
    
    # Get the test code
    test_code = test_case.test_code
    
    try:
        # Create a safe execution environment
        test_globals = {
            'student_code': student_code,  # <-- THIS IS THE KEY!
            'unittest': __import__('unittest'),
            'io': __import__('io'),
            'sys': __import__('sys'),
            'redirect_stdout': redirect_stdout,
            '__builtins__': {
                'len': len, 'str': str, 'int': int, 'float': float,
                'list': list, 'dict': dict, 'tuple': tuple,
                'range': range, 'print': print, 'Exception': Exception,
                # ... other safe built-ins
            }
        }
        
        # Capture output
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
            # Execute the test code with student_code available
            exec(test_code, test_globals)
        
        # If we get here, all tests passed
        return True
        
    except AssertionError:
        # Test failed
        return False
    except Exception as e:
        # Error in execution
        print(f"Execution error: {e}")
        return False
```

## What You Put in Admin vs What Gets Executed:

### In Admin Panel (TestCase.test_code):
```python
import unittest

try:
    exec(student_code)  # This will be populated automatically
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestAddNumbers(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(add_numbers(2, 3), 5)

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
```

### What Actually Gets Executed:
```python
# System automatically provides:
student_code = "def add_numbers(a, b):\n    return a + b"

# Then your test code runs with student_code available:
import unittest

try:
    exec(student_code)  # Now student_code is defined!
    # This creates: def add_numbers(a, b): return a + b
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")

class TestAddNumbers(unittest.TestCase):
    def test_basic(self):
        # Now add_numbers is available because exec(student_code) defined it
        self.assertEqual(add_numbers(2, 3), 5)  # This works!

if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
```

## Summary:

- **You DON'T define `student_code`** in the admin panel
- **The system provides it automatically** when running tests
- **`student_code` contains the actual code** the student submitted
- **`exec(student_code)` makes the student's functions/classes available** for testing
- **Your test methods can then call the student's functions** to verify they work correctly

The `student_code` variable is the bridge between what the student submitted and what your tests are checking!
