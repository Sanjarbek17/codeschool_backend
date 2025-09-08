# Secure Test Code Examples for Admin Panel

This document provides secure test code examples that work with the `AutomatedTestRunner` system in your Django application. These examples do NOT use the dangerous `exec()` function directly.

## How the Secure System Works

Your `AutomatedTestRunner` class in `apps/editor/services.py`:
1. **Combines** student code with test code safely
2. **Executes** in a sandboxed environment with resource limits
3. **Captures** output and compares with expected results
4. **Prevents** dangerous imports and operations

## Key Differences from Previous Examples

❌ **OLD (Insecure)**: Used `exec(student_code)` directly
✅ **NEW (Secure)**: Student code is combined automatically by the system

## Updated Test Code Examples for Admin Panel

### Example 1: Simple Function Test (SECURE)

**For testing a function like `add_numbers(a, b)`:**

```
# Test the add_numbers function
result1 = add_numbers(2, 3)
print(result1)

result2 = add_numbers(-2, -3)
print(result2)

result3 = add_numbers(0, 0)
print(result3)

result4 = add_numbers(10, 15)
print(result4)
```

**Admin Panel Fields:**
- **Input data**: "Various number pairs for testing"
- **Expected output**: 
```
5
-5
0
25
```

### Example 2: Calculator Class Test (SECURE)

**For testing a Calculator class:**

```
# Test Calculator class
calc = Calculator()

# Test addition
add_result = calc.add(2, 3)
print(f"add: {add_result}")

# Test subtraction
sub_result = calc.subtract(5, 3)
print(f"subtract: {sub_result}")

# Test multiplication
mul_result = calc.multiply(3, 4)
print(f"multiply: {mul_result}")

# Test division
div_result = calc.divide(10, 2)
print(f"divide: {div_result}")

# Test division by zero handling
try:
    calc.divide(5, 0)
    print("divide_by_zero: ERROR - should have raised exception")
except ZeroDivisionError:
    print("divide_by_zero: OK")
```

**Admin Panel Fields:**
- **Input data**: "Calculator operations"
- **Expected output**:
```
add: 5
subtract: 2
multiply: 12
divide: 5.0
divide_by_zero: OK
```

### Example 3: Prime Number Function Test (SECURE)

**For testing an `is_prime(n)` function:**

```
# Test prime number function
test_numbers = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

for num in test_numbers:
    result = is_prime(num)
    print(f"{num}: {result}")
```

**Admin Panel Fields:**
- **Input data**: "Numbers 2-11 for prime testing"
- **Expected output**:
```
2: True
3: True
4: False
5: True
6: False
7: True
8: False
9: False
10: False
11: True
```

### Example 4: List Operations Test (SECURE)

**For testing a `sort_list(lst)` function:**

```
# Test sorting function
test_cases = [
    [3, 1, 4, 1, 5],
    [5, 4, 3, 2, 1],
    [],
    [42]
]

for i, test_list in enumerate(test_cases):
    result = sort_list(test_list.copy())  # Use copy to avoid modifying original
    print(f"Test {i+1}: {result}")
```

**Admin Panel Fields:**
- **Input data**: "Various lists to sort"
- **Expected output**:
```
Test 1: [1, 1, 3, 4, 5]
Test 2: [1, 2, 3, 4, 5]
Test 3: []
Test 4: [42]
```

### Example 5: String Operations Test (SECURE)

**For testing a `reverse_string(s)` function:**

```
# Test string reversal
test_strings = ["hello", "python", "", "a", "racecar"]

for s in test_strings:
    result = reverse_string(s)
    print(f"'{s}' -> '{result}'")
```

**Admin Panel Fields:**
- **Input data**: "Various strings to reverse"
- **Expected output**:
```
'hello' -> 'olleh'
'python' -> 'nohtyp'
'' -> ''
'a' -> 'a'
'racecar' -> 'racecar'
```

### Example 6: Math Operations Test (SECURE)

**For testing a `factorial(n)` function:**

```
# Test factorial function
test_numbers = [0, 1, 2, 3, 4, 5, 6]

for num in test_numbers:
    result = factorial(num)
    print(f"{num}! = {result}")
```

**Admin Panel Fields:**
- **Input data**: "Numbers 0-6 for factorial calculation"
- **Expected output**:
```
0! = 1
1! = 1
2! = 2
3! = 6
4! = 24
5! = 120
6! = 720
```

### Example 7: Error Handling Test (SECURE)

**For testing error handling in functions:**

```
# Test error handling
try:
    result = divide_safe(10, 2)
    print(f"Normal division: {result}")
except Exception as e:
    print(f"Unexpected error: {e}")

try:
    result = divide_safe(10, 0)
    print(f"Division by zero result: {result}")
except ZeroDivisionError:
    print("Division by zero handled correctly")
except Exception as e:
    print(f"Other error: {e}")

try:
    result = divide_safe("invalid", 2)
    print(f"Invalid input result: {result}")
except TypeError:
    print("Type error handled correctly")
except Exception as e:
    print(f"Other error: {e}")
```

**Admin Panel Fields:**
- **Input data**: "Test error handling scenarios"
- **Expected output**:
```
Normal division: 5.0
Division by zero handled correctly
Type error handled correctly
```

### Example 8: Multiple Function Test (SECURE)

**For testing multiple functions in one test case:**

```
# Test multiple functions
print("=== Math Functions Test ===")

# Test addition
add_result = add_two_numbers(5, 3)
print(f"Addition: 5 + 3 = {add_result}")

# Test multiplication
mult_result = multiply_two_numbers(4, 6)
print(f"Multiplication: 4 * 6 = {mult_result}")

# Test power
power_result = power_of_two(3)
print(f"Power: 2^3 = {power_result}")

print("=== All tests completed ===")
```

**Admin Panel Fields:**
- **Input data**: "Multiple math function tests"
- **Expected output**:
```
=== Math Functions Test ===
Addition: 5 + 3 = 8
Multiplication: 4 * 6 = 24
Power: 2^3 = 8
=== All tests completed ===
```

## Key Principles for Secure Test Code

### 1. Direct Function Calls
Instead of using unittest framework, directly call the functions and print results:

```
# SECURE: Direct function call
result = my_function(input)
print(result)
```

### 2. Expected Output Matching
The system compares actual output with expected output in the admin panel:

- **Test code** prints the actual results
- **Expected output field** contains what should be printed
- **System compares** them automatically

### 3. Error Testing
Test error handling by using try/except blocks:

```
# Test error handling
try:
    risky_function(bad_input)
    print("ERROR: Should have raised exception")
except ExpectedException:
    print("OK: Exception handled correctly")
```

### 4. Formatted Output
Use consistent formatting for easier comparison:

```
# Good: Consistent formatting
print(f"Result: {value}")
print(f"Status: {'PASS' if condition else 'FAIL'}")
```

## Admin Panel Form Filling

### Field: Test code
Copy one of the secure examples above (without the markdown code blocks)

### Field: Input data
Describe what inputs are being tested, e.g.:
- "Two integers for addition"
- "List of numbers for sorting"
- "String for reversal"

### Field: Expected output
Copy the exact output that should be printed, e.g.:
```
5
-5
0
25
```

### Field: Timeout seconds
Recommended values:
- Simple functions: 10-15 seconds
- Complex algorithms: 30-60 seconds
- File operations: 45-90 seconds

## Testing Your Test Cases

Before saving, mentally trace through:
1. **Student writes function** (e.g., `add_numbers`)
2. **Your test code calls it** (e.g., `add_numbers(2, 3)`)
3. **System captures output** (e.g., prints `5`)
4. **System compares** with your expected output
5. **Test passes/fails** based on match

## Common Mistakes to Avoid

❌ **Don't use** `exec()` or `eval()`
❌ **Don't use** `unittest` framework
❌ **Don't try** to import student code
❌ **Don't forget** to print results
❌ **Don't use** inconsistent output formatting

✅ **Do call** functions directly
✅ **Do print** clear results
✅ **Do test** edge cases
✅ **Do use** try/except for error testing
✅ **Do match** expected output exactly
