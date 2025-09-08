# Django Admin Panel - TestCase Creation Example

## What you'll see in the admin panel:

```
Add test case

Task: [Dropdown to select task] *
Test code: [Large text area - paste code here] *
Hidden: ☐ (checkbox)
Input data: [Text field]
Expected output: [Text field]  
Timeout seconds: [30] *

[Save and add another] [Save and continue editing] [Save]
```

## Example of filling out the form:

### Field: Task
**Select:** "Homework 1 - Task 1: Create add_numbers function"

### Field: Test code
**Paste this exactly (SECURE VERSION):**
```
# Test the add_numbers function
result1 = add_numbers(2, 3)
print(result1)

result2 = add_numbers(10, 15)
print(result2)

result3 = add_numbers(-2, -3)
print(result3)

result4 = add_numbers(-10, 5)
print(result4)

result5 = add_numbers(0, 0)
print(result5)

result6 = add_numbers(5, 0)
print(result6)
```

### Field: Hidden
**Check:** ☐ (leave unchecked for visible test, check for hidden test)

### Field: Input data
**Type:** "Two numbers: a and b (integers or floats)"

### Field: Expected output
**Type:**
```
5
25
-5
-5
0
5
```

### Field: Timeout seconds
**Type:** "30"

## Step-by-step process:

1. **Login to admin** at `http://yoursite.com/admin/`
2. **Navigate** to "Submissions" section
3. **Click** "Test cases"
4. **Click** "Add test case" button
5. **Fill the form** as shown above
6. **Click** "Save"

## Multiple test cases for one task

You can create multiple test cases for the same task:

### Test Case 1 (Visible to students):
- Basic functionality test
- Simple test cases students can see

### Test Case 2 (Hidden from students):
- Edge cases and advanced testing
- Students can't see these until after submission

## Common mistakes to avoid:

❌ **Don't include** markdown code blocks (```)
❌ **Don't use** `exec(student_code)` - the system handles this securely
❌ **Don't use** unittest framework - use direct function calls
❌ **Don't use** wrong function/class names
❌ **Don't try to define** `student_code` - it's provided automatically

✅ **Do call** functions directly in your test code
✅ **Do print** results for output comparison
✅ **Do use** correct function names that match the assignment
✅ **Do test** multiple scenarios (positive, negative, edge cases)
✅ **Do understand** that your system combines student code with test code securely

## Quick Copy-Paste Examples for Common Tasks:

### For a function that returns a value:
```
# Test the function
result1 = function_name(input1)
print(result1)

result2 = function_name(input2)
print(result2)
```

### For a class with methods:
```
# Test the class
obj = ClassName()
result1 = obj.method_name(input1)
print(result1)

result2 = obj.method_name(input2)
print(result2)
```

### For output testing (programs that already print):
```
# No additional test code needed if the student's program already prints
# Just set expected output to what should be printed
```

### For error handling testing:
```
# Test error handling
try:
    result = risky_function(bad_input)
    print("ERROR: Should have thrown exception")
except ExpectedException:
    print("OK: Exception handled correctly")
```
