# 🧪 Automated Testing System Documentation

## Overview

The CodeSchool Backend now includes a comprehensive automated testing system that evaluates student code submissions against predefined test cases. This system provides immediate feedback to students and reduces manual grading workload for teachers.

## 🏗️ **System Architecture**

### Components

1. **SecureCodeExecutor** - Secure, sandboxed code execution engine
2. **AutomatedTestRunner** - Service for running test cases against submissions
3. **Enhanced Views** - API endpoints for testing and submission
4. **Management Commands** - Bulk testing utilities
5. **Security Layer** - Import restrictions and resource limits

## 🚀 **Key Features**

### ✅ **Security Features**
- **Sandboxed Execution**: Code runs in isolated processes
- **Resource Limits**: Memory and CPU time restrictions
- **Import Restrictions**: Prevents dangerous module imports
- **Timeout Protection**: Prevents infinite loops and long-running code
- **File System Protection**: Restricted file access

### 🧪 **Testing Capabilities**
- **Automatic Testing**: Tests run automatically on submission
- **Manual Re-testing**: Teachers can re-run tests anytime
- **Visible/Hidden Tests**: Support for public and private test cases
- **Detailed Results**: Execution time, memory usage, and error details
- **Batch Processing**: Bulk testing of multiple submissions

### 📊 **Performance Monitoring**
- **Execution Time Tracking**: Measures code performance
- **Memory Usage Monitoring**: Tracks resource consumption
- **Test Result Analytics**: Success rates and difficulty analysis
- **Progress Tracking**: Student improvement over time

## 🔧 **Configuration**

### Settings (in `core/settings.py`)

```python
AUTOMATED_TESTING = {
    'DEFAULT_TIMEOUT': 30,           # Execution timeout (seconds)
    'MEMORY_LIMIT_MB': 128,          # Memory limit (MB)
    'AUTO_TEST_ON_SUBMISSION': True,  # Auto-test on submission
    'MAX_CODE_SIZE': 1024 * 1024,    # Max code file size (bytes)
    'SHOW_DETAILED_ERRORS': True,    # Show errors to students
    'MAX_TEST_CASES_PER_TASK': 50,   # Max test cases per task
}
```

## 📡 **API Endpoints**

### 1. **Code Execution** - `/api/editor/execute/`

**Enhanced secure code execution with detailed results.**

```bash
POST /api/editor/execute/
Content-Type: application/json
Authorization: Token <your_token>

{
    "code": "print('Hello World!')",
    "timeout": 30,
    "input_data": ""
}
```

**Response:**
```json
{
    "success": true,
    "output": "Hello World!\n",
    "error": "",
    "execution_time": 0.001,
    "memory_usage": 1024,
    "timeout": false
}
```

### 2. **Test Code Against Task** - `/api/editor/test/`

**Test student code against visible test cases for immediate feedback.**

```bash
POST /api/editor/test/
Content-Type: application/json
Authorization: Token <your_token>

{
    "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
    "task_id": 1
}
```

**Response:**
```json
{
    "task_title": "Calculate Factorial",
    "total_tests": 3,
    "passed_tests": 2,
    "success_rate": 66.7,
    "test_results": [
        {
            "test_id": 1,
            "passed": true,
            "output": "120",
            "error": "",
            "execution_time": 0.001,
            "hidden": false
        }
    ]
}
```

### 3. **Submit Homework with Auto-Testing** - `/api/submissions/submissions/`

**Create submission with automatic testing.**

```bash
POST /api/submissions/submissions/
Content-Type: application/json
Authorization: Token <your_token>

{
    "task": 1,
    "code_text": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
    "auto_test": true
}
```

**Response:**
```json
{
    "id": 1,
    "task": 1,
    "student": 1,
    "code_text": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
    "submitted_at": "2025-09-08T10:30:00Z",
    "passed_tests": 3,
    "total_tests": 5,
    "success_rate": 60.0,
    "is_successful": false,
    "execution_time": 0.045,
    "memory_usage": 2048,
    "test_results": {
        "auto_tested": true,
        "total_tests": 5,
        "passed_tests": 3,
        "success_rate": 60.0,
        "individual_results": [...]
    }
}
```

### 4. **Re-test Submission** - `/api/submissions/submissions/{id}/auto_test/`

**Teachers can re-run automated tests on any submission.**

```bash
POST /api/submissions/submissions/1/auto_test/
Authorization: Token <teacher_token>
```

**Response:**
```json
{
    "submission_id": 1,
    "student_name": "John Doe",
    "task_title": "Calculate Factorial",
    "previous_score": {
        "passed_tests": 2,
        "total_tests": 5,
        "success_rate": 40.0
    },
    "new_score": {
        "passed_tests": 3,
        "total_tests": 5,
        "success_rate": 60.0
    },
    "execution_details": {
        "execution_time": 0.045,
        "memory_usage": 2048
    },
    "updated": true
}
```

## 🛠️ **Management Commands**

### Bulk Testing Command

**Re-test existing submissions in bulk:**

```bash
# Test all untested submissions
python manage.py run_automated_tests

# Test all submissions for a specific task
python manage.py run_automated_tests --task-id 1

# Test all submissions for a specific student  
python manage.py run_automated_tests --student-id 1

# Re-test all submissions (including previously tested)
python manage.py run_automated_tests --retest-all

# Dry run to see what would be tested
python manage.py run_automated_tests --dry-run

# Process in smaller batches
python manage.py run_automated_tests --batch-size 5
```

## 👩‍🏫 **Teacher Workflow**

### 1. **Create Test Cases**

Teachers create test cases through the admin or API:

```python
# Example test case for factorial function
{
    "task": 1,
    "test_code": "assert factorial(5) == 120",
    "hidden": false,
    "input_data": "5",
    "expected_output": "120",
    "timeout_seconds": 10
}
```

### 2. **Monitor Submissions**

- View real-time submission results with automatic scores
- Re-test submissions when test cases are updated
- Access detailed analytics and student progress

### 3. **Bulk Operations**

- Use management commands for bulk testing
- Update test cases and re-evaluate all submissions
- Generate progress reports and analytics

## 👨‍🎓 **Student Workflow**

### 1. **Code Development**

Students can test their code against visible test cases:

```bash
# Test code before submission
POST /api/editor/test/
{
    "code": "student_code_here",
    "task_id": 1
}
```

### 2. **Submission**

Submit homework with automatic testing:

```bash
# Submit with auto-testing (default)
POST /api/submissions/submissions/
{
    "task": 1,
    "code_text": "student_solution",
    "auto_test": true
}
```

### 3. **Immediate Feedback**

- Get instant test results upon submission
- See which test cases passed/failed
- View execution time and memory usage
- Understand performance characteristics

## 🔒 **Security Considerations**

### Code Execution Security

1. **Process Isolation**: Each code execution runs in a separate process
2. **Resource Limits**: Memory and CPU time restrictions prevent abuse
3. **Import Restrictions**: Dangerous modules are blocked
4. **Timeout Protection**: Prevents infinite loops and DoS attacks
5. **File System Protection**: Limited file access permissions

### Restricted Imports

The following imports are blocked for security:

```python
RESTRICTED_IMPORTS = {
    'os', 'sys', 'subprocess', 'shutil', 'glob', 'pickle', 'socket', 
    'urllib', 'requests', 'http', 'ftplib', 'smtplib', 'email',
    'multiprocessing', 'threading', 'asyncio', 'concurrent',
    '__import__', 'eval', 'exec', 'compile', 'open', 'file',
    'input', 'raw_input'
}
```

### Safe Built-ins

Only safe built-in functions are available:

```python
SAFE_BUILTINS = {
    'print', 'len', 'range', 'str', 'int', 'float', 'bool',
    'list', 'dict', 'set', 'tuple', 'abs', 'max', 'min', 'sum',
    'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
    'any', 'all', 'round', 'pow', 'divmod', 'ord', 'chr',
    'bin', 'hex', 'oct', 'isinstance', 'issubclass', 'type'
}
```

## 📈 **Performance Considerations**

### Resource Management

- **Memory Limit**: Default 128MB per execution
- **CPU Timeout**: Default 30 seconds per test
- **Concurrent Executions**: Uses multiprocessing for isolation
- **Batch Processing**: Configurable batch sizes for bulk operations

### Optimization Tips

1. **Test Case Design**: Keep test cases simple and fast
2. **Timeout Settings**: Adjust based on task complexity
3. **Hidden Tests**: Use sparingly to avoid overloading system
4. **Batch Size**: Adjust based on server resources

## 🐛 **Troubleshooting**

### Common Issues

1. **Timeout Errors**: Increase timeout for complex algorithms
2. **Memory Errors**: Check for memory leaks in student code
3. **Import Errors**: Student trying to use restricted modules
4. **Test Failures**: Review test case logic and expected outputs

### Debug Mode

Enable detailed error messages for debugging:

```python
AUTOMATED_TESTING = {
    'SHOW_DETAILED_ERRORS': True,  # Show full error traces
}
```

### Logging

Check Django logs for execution details:

```bash
# View recent test executions
tail -f logs/django.log | grep "AutomatedTestRunner"
```

## 🔮 **Future Enhancements**

### Planned Features

1. **Language Support**: Support for Java, C++, JavaScript
2. **Advanced Analytics**: Machine learning-based difficulty analysis
3. **Real-time Testing**: WebSocket-based live code testing
4. **Code Quality Metrics**: Style and efficiency scoring
5. **Plagiarism Detection**: Code similarity analysis
6. **Interactive Debugging**: Step-through execution for students

### Integration Opportunities

1. **IDE Integration**: Direct connection with VS Code/PyCharm
2. **Git Integration**: Automatic testing on commits
3. **CI/CD Pipeline**: Integration with GitHub Actions
4. **LMS Integration**: Connection with Canvas/Moodle
5. **Mobile App**: Testing from mobile devices

## 📚 **Additional Resources**

- **API Documentation**: `/api/docs/` (Swagger UI)
- **Admin Interface**: `/admin/` (Django Admin)
- **Source Code**: `apps/editor/services.py`
- **Test Cases**: `apps/submissions/models.py`
- **Management Commands**: `apps/submissions/management/commands/`

---

**Note**: This automated testing system is designed for educational purposes and includes appropriate security measures for a learning environment. For production use, additional security hardening may be required based on specific deployment requirements.
