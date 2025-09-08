# Common Test Execution Errors and Solutions

## Error: `name 'solve_problem' is not defined`

### Problem Description
When testing code against task test cases, you might encounter `NameError: name 'solve_problem' is not defined` or similar errors.

### Root Cause Analysis

The error occurs due to mismatches between:

1. **Function names** in your code vs. what the test expects
2. **Function signatures** (parameters) between your implementation and test calls
3. **Expected output** vs. actual output from your functions

### Example of the Problem

**Your Code (WRONG):**
```python
def add_numbers():  # No parameters
    result = 'Hello World'
    return result

print(solve_problem())  # Calls undefined function
```

**Test Case Expectations:**
- Function name: `add_numbers(a, b)` with two parameters
- Test calls: `add_numbers(2, 3)`, `add_numbers(10, 15)`, etc.
- Expected outputs: `5`, `25`, `-5`, `-5`, `0`, `5`

### How to Fix

#### Step 1: Check the Task Requirements
Look at the test case for task 15:

```python
# Test code expects:
result1 = add_numbers(2, 3)     # Should return 5
result2 = add_numbers(10, 15)   # Should return 25
result3 = add_numbers(-2, -3)   # Should return -5
# etc.
```

#### Step 2: Implement the Correct Function

**Correct Implementation:**
```python
def add_numbers(a, b):
    return a + b
```

#### Step 3: Test Your Implementation

**HTTP Request (CORRECT):**
```json
{
    "task_id": 15,
    "code": "def add_numbers(a, b):\n    return a + b"
}
```

### Understanding Your System's Test Flow

1. **Student submits code** → Contains function definition
2. **System gets test case** → Contains test code that calls the function
3. **System combines them:**
   ```python
   # Student code
   def add_numbers(a, b):
       return a + b
   
   # Test case execution
   result1 = add_numbers(2, 3)
   print(result1)
   # ... more test calls
   ```
4. **System executes** combined code securely
5. **System compares** actual output with expected output

### Common Mistakes and Fixes

#### Mistake 1: Wrong Function Name
```python
# WRONG
def solve_problem():  # Test expects 'add_numbers'
    return "Hello"

# CORRECT
def add_numbers(a, b):  # Matches test expectations
    return a + b
```

#### Mistake 2: Wrong Function Signature
```python
# WRONG
def add_numbers():  # No parameters, but test calls add_numbers(2, 3)
    return 5

# CORRECT
def add_numbers(a, b):  # Two parameters as expected
    return a + b
```

#### Mistake 3: Calling Undefined Functions
```python
# WRONG
def add_numbers(a, b):
    return a + b

print(solve_problem())  # 'solve_problem' not defined

# CORRECT
def add_numbers(a, b):
    return a + b
# Let the test code handle the function calls
```

#### Mistake 4: Wrong Return Type/Value
```python
# WRONG
def add_numbers(a, b):
    return "Hello World"  # Returns string, test expects numbers

# CORRECT
def add_numbers(a, b):
    return a + b  # Returns number as expected
```

### How to Debug Test Failures

#### Method 1: Check Task Details
```bash
# Get task information
GET /api/assignments/tasks/15/

# Check what the task description says
```

#### Method 2: Check Test Cases
```bash
# Get visible test cases for the task
GET /api/submissions/test-cases/?task=15

# See what functions and outputs are expected
```

#### Method 3: Test with Simple Implementation
```python
# Start with the most basic implementation
def add_numbers(a, b):
    return a + b
```

#### Method 4: Check Expected vs Actual Output
When testing fails, look at the response:
```json
{
  "test_results": [
    {
      "passed": false,
      "output": "Your actual output",
      "error": "Error message if any",
      "expected": "Expected output"
    }
  ]
}
```

### Best Practices for Test Success

1. **Read the task description carefully**
2. **Check function names** in any provided examples
3. **Look at test case patterns** to understand expected behavior
4. **Start simple** - implement basic functionality first
5. **Test incrementally** - verify each piece works
6. **Match expected output exactly** - whitespace and formatting matter

### Example: Complete Correct Implementation

For task 15 which expects `add_numbers(a, b)`:

**HTTP Request:**
```json
{
    "task_id": 15,
    "code": "def add_numbers(a, b):\n    \"\"\"Add two numbers and return the result.\"\"\"\n    return a + b"
}
```

**Expected Response:**
```json
{
    "task_title": "Task 4: Design an experiment - From",
    "total_tests": 1,
    "passed_tests": 1,
    "success_rate": 100.0,
    "test_results": [
        {
            "test_id": 1,
            "passed": true,
            "output": "5\n25\n-5\n-5\n0\n5",
            "error": "",
            "execution_time": 0.001,
            "memory_usage": 1024,
            "timeout": false,
            "hidden": false
        }
    ]
}
```

### Quick Fix Checklist

When you get a "name not defined" error:

- [ ] Check if function name matches test expectations
- [ ] Verify function takes correct number of parameters
- [ ] Ensure you're not calling undefined functions
- [ ] Remove any `print()` calls for functions (let test handle output)
- [ ] Match the expected function behavior exactly

Remember: The test system combines your code with test code, so focus on implementing the required functions correctly rather than trying to handle the testing yourself!
