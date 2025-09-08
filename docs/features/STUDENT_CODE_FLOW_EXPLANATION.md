# Understanding the Student Code Flow

## Where does `student_code` come from?

The `student_code` variable represents the code that students submit through your platform. Here's the complete flow:

## 1. Student Submission Process

```
Student writes code → Submits via web interface → Stored in HomeworkSubmission.code_text
```

### Example Student Submission:
```python
def add_numbers(a, b):
    return a + b
```

This gets stored in the database in the `HomeworkSubmission` model's `code_text` field.

## 2. Test Execution Flow

When you want to test the student's code, here's what happens:

```
AutomatedTestRunner.run_submission_tests(submission)
    ↓
_run_single_test(student_code, test_case)
    ↓
SecureCodeExecutor.execute_code(combined_code)
```

## 3. Code Combination Process

Your system in `apps/editor/services.py` does this:

```python
def _run_single_test(self, student_code: str, test_case) -> TestResult:
    # student_code comes from submission.code_text
    # test_case.test_code comes from admin panel
    
    combined_code = f"""
{student_code}

# Test case execution
{test_case.test_code}
"""
    
    # Execute the combined code securely
    result = executor.execute_code(combined_code, test_case.input_data)
```

## 4. Example of Combined Code

### Student Code (from submission):
```python
def add_numbers(a, b):
    return a + b
```

### Your Test Code (from admin panel):
```python
# Test the add_numbers function
result1 = add_numbers(2, 3)
print(result1)

result2 = add_numbers(-2, -3)
print(result2)
```

### Combined Code (what actually executes):
```python
def add_numbers(a, b):
    return a + b

# Test case execution
# Test the add_numbers function
result1 = add_numbers(2, 3)
print(result1)

result2 = add_numbers(-2, -3)
print(result2)
```

## 5. Security Measures in Your System

Your `SecureCodeExecutor` class provides:

- **Process isolation** using multiprocessing
- **Resource limits** (memory, CPU time, file size)
- **Restricted imports** (no dangerous modules)
- **Timeout protection** (prevents infinite loops)
- **Restricted builtins** (only safe functions available)

## 6. Why the Old Examples Were Dangerous

### ❌ Insecure Approach (OLD):
```python
# This was in the old examples - DANGEROUS!
try:
    exec(student_code)  # Direct execution without sandboxing
except Exception as e:
    raise AssertionError(f"Code execution failed: {e}")
```

Problems:
- No sandboxing
- No resource limits
- Student could import dangerous modules
- Could execute system commands
- Could access file system
- Could cause infinite loops

### ✅ Secure Approach (YOUR SYSTEM):
```python
# Your system does this safely
def execute_code(self, code: str, test_input: str = ""):
    # Uses multiprocessing for isolation
    # Sets resource limits
    # Restricts available builtins
    # Implements timeout protection
    # Prevents dangerous imports
```

## 7. How to Write Test Code for Admin Panel

Since your system handles the code combination securely, you just need to write test code that:

1. **Calls the student's functions directly**
2. **Prints the results**
3. **Tests various scenarios**

### Example Template:
```python
# Test the function_name function
result1 = function_name(test_input_1)
print(result1)

result2 = function_name(test_input_2)
print(result2)

# Test edge cases
result3 = function_name(edge_case_input)
print(result3)
```

## 8. Complete Example Walkthrough

### Student Task:
"Write a function `multiply(a, b)` that returns the product of two numbers"

### Student Submission (stored in database):
```python
def multiply(a, b):
    return a * b
```

### Your Test Code (in admin panel):
```python
# Test multiplication function
result1 = multiply(3, 4)
print(result1)

result2 = multiply(-2, 5)
print(result2)

result3 = multiply(0, 10)
print(result3)
```

### Expected Output (in admin panel):
```
12
-10
0
```

### What Actually Runs (combined by system):
```python
def multiply(a, b):
    return a * b

# Test case execution
# Test multiplication function
result1 = multiply(3, 4)
print(result1)

result2 = multiply(-2, 5)
print(result2)

result3 = multiply(0, 10)
print(result3)
```

### Output Captured by System:
```
12
-10
0
```

### Test Result:
✅ **PASS** - Output matches expected output

## 9. Key Takeaways

1. **You don't need** to worry about `student_code` variable
2. **Your system handles** the code combination securely
3. **Just write test code** that calls functions and prints results
4. **The system compares** actual output with expected output
5. **Everything runs** in a secure, sandboxed environment

## 10. Database Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Student       │    │  HomeworkSub-   │    │   TestCase      │
│   Submits Code  │───▶│  mission Model  │    │   Model         │
│                 │    │  .code_text     │    │  .test_code     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────────────────────────────┐
                       │    AutomatedTestRunner              │
                       │    Combines & Executes Securely        │
                       └─────────────────────────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────────┐
                              │   Test Results          │
                              │   Update Submission     │
                              │   .passed_tests         │
                              │   .total_tests          │
                              └─────────────────────────┘
```

This is why your secure system is much better than using `exec()` directly!
