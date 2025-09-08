"""
Automated Code Testing Services for CodeSchool Backend

This module provides secure and automated testing capabilities for student code submissions.
It integrates with the existing editor app and submissions system to provide automated
evaluation of homework submissions against predefined test cases.
"""

import sys
import io
import subprocess
import tempfile
import os
import signal
import time
import traceback
import resource
import multiprocessing
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from django.conf import settings


@dataclass
class TestResult:
    """Data class to represent the result of a single test case execution."""

    passed: bool
    output: str
    error: str = ""
    execution_time: float = 0.0
    memory_usage: int = 0  # in KB
    timeout: bool = False


@dataclass
class SubmissionTestResults:
    """Data class to represent the results of all test cases for a submission."""

    total_tests: int
    passed_tests: int
    test_results: List[TestResult]
    overall_execution_time: float
    max_memory_usage: int
    success_rate: float


class SecureCodeExecutor:
    """
    Secure code execution engine with sandboxing and resource limits.

    Features:
    - Process isolation with multiprocessing
    - Timeout protection
    - Memory and CPU limits
    - Restricted file system access
    - Import restrictions for security
    """

    # Restricted imports for security
    RESTRICTED_IMPORTS = {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "glob",
        "pickle",
        "socket",
        "urllib",
        "requests",
        "http",
        "ftplib",
        "smtplib",
        "email",
        "multiprocessing",
        "threading",
        "asyncio",
        "concurrent",
        "__import__",
        "eval",
        "exec",
        "compile",
        "open",
        "file",
        "input",
        "raw_input",
    }

    def __init__(self, timeout_seconds: int = 30, memory_limit_mb: int = 128):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb

    def _set_resource_limits(self):
        """Set resource limits for the executing process."""
        try:
            # Memory limit (in bytes)
            memory_limit = self.memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

            # CPU time limit (in seconds)
            resource.setrlimit(
                resource.RLIMIT_CPU, (self.timeout_seconds, self.timeout_seconds)
            )

            # File size limit (1MB)
            file_limit = 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))

        except (OSError, ValueError) as e:
            # Resource limits might not be available on all systems
            print(f"Warning: Could not set resource limits: {e}")

    def _validate_code_security(self, code: str) -> Tuple[bool, str]:
        """
        Basic security validation of code before execution.

        Returns:
            Tuple of (is_safe: bool, error_message: str)
        """
        code_lower = code.lower()

        # Check for restricted imports
        for restricted in self.RESTRICTED_IMPORTS:
            if (
                f"import {restricted}" in code_lower
                or f"from {restricted}" in code_lower
            ):
                return False, f"Restricted import detected: {restricted}"

        # Check for dangerous function calls
        dangerous_patterns = [
            "exec(",
            "eval(",
            "__import__",
            "compile(",
            "open(",
            "file(",
            "input(",
            "raw_input(",
            "getattr(",
            "setattr(",
            "delattr(",
            "hasattr(",
            "globals(",
            "locals(",
            "vars(",
            "dir(",
        ]

        for pattern in dangerous_patterns:
            if pattern in code_lower:
                return (
                    False,
                    f"Potentially dangerous function call detected: {pattern.rstrip('(')}",
                )

        return True, ""

    def _execute_code_in_process(
        self, code: str, test_input: str = ""
    ) -> Dict[str, Any]:
        """
        Execute code in a separate process with security restrictions.
        This function runs in the child process.
        """
        try:
            # Set resource limits
            self._set_resource_limits()

            # Capture both stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            new_stdout = io.StringIO()
            new_stderr = io.StringIO()

            # Redirect stdin if test input is provided
            if test_input:
                old_stdin = sys.stdin
                sys.stdin = io.StringIO(test_input)

            sys.stdout = new_stdout
            sys.stderr = new_stderr

            start_time = time.time()

            # Create restricted globals
            restricted_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "abs": abs,
                    "max": max,
                    "min": min,
                    "sum": sum,
                    "sorted": sorted,
                    "reversed": reversed,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "any": any,
                    "all": all,
                    "round": round,
                    "pow": pow,
                    "divmod": divmod,
                    "ord": ord,
                    "chr": chr,
                    "bin": bin,
                    "hex": hex,
                    "oct": oct,
                    "isinstance": isinstance,
                    "issubclass": issubclass,
                    "type": type,
                    "Exception": Exception,
                    "ValueError": ValueError,
                    "TypeError": TypeError,
                    "IndexError": IndexError,
                    "KeyError": KeyError,
                    "AttributeError": AttributeError,
                    "ZeroDivisionError": ZeroDivisionError,
                }
            }

            # Execute the code
            exec(code, restricted_globals)

            execution_time = time.time() - start_time

            # Get memory usage (approximate)
            try:
                memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                # Convert to KB (Linux reports in KB, macOS in bytes)
                if sys.platform == "darwin":  # macOS
                    memory_usage = memory_usage // 1024
            except:
                memory_usage = 0

            result = {
                "success": True,
                "output": new_stdout.getvalue(),
                "error": new_stderr.getvalue(),
                "execution_time": execution_time,
                "memory_usage": memory_usage,
                "timeout": False,
            }

            return result

        except Exception as e:
            execution_time = time.time() - start_time if "start_time" in locals() else 0
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time": execution_time,
                "memory_usage": 0,
                "timeout": False,
            }
        finally:
            # Restore stdout, stderr, stdin
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            if test_input and "old_stdin" in locals():
                sys.stdin = old_stdin

    def execute_code(self, code: str, test_input: str = "") -> TestResult:
        """
        Execute code safely with timeout and resource limits.

        Args:
            code: The Python code to execute
            test_input: Optional input to provide to the code

        Returns:
            TestResult object containing execution results
        """
        # Validate code security
        is_safe, security_error = self._validate_code_security(code)
        if not is_safe:
            return TestResult(
                passed=False,
                output="",
                error=f"Security violation: {security_error}",
                execution_time=0.0,
                memory_usage=0,
                timeout=False,
            )

        # Use multiprocessing for isolation
        manager = multiprocessing.Manager()
        result_dict = manager.dict()

        def target():
            try:
                result = self._execute_code_in_process(code, test_input)
                result_dict.update(result)
            except Exception as e:
                result_dict.update(
                    {
                        "success": False,
                        "output": "",
                        "error": f"Process execution error: {str(e)}",
                        "execution_time": 0,
                        "memory_usage": 0,
                        "timeout": False,
                    }
                )

        process = multiprocessing.Process(target=target)
        process.start()
        process.join(timeout=self.timeout_seconds)

        if process.is_alive():
            process.terminate()
            process.join()
            return TestResult(
                passed=False,
                output="",
                error="Code execution timed out",
                execution_time=self.timeout_seconds,
                memory_usage=0,
                timeout=True,
            )

        # Process completed within timeout
        if result_dict.get("success", False):
            return TestResult(
                passed=True,
                output=result_dict.get("output", ""),
                error=result_dict.get("error", ""),
                execution_time=result_dict.get("execution_time", 0),
                memory_usage=result_dict.get("memory_usage", 0),
                timeout=False,
            )
        else:
            return TestResult(
                passed=False,
                output=result_dict.get("output", ""),
                error=result_dict.get("error", "Unknown execution error"),
                execution_time=result_dict.get("execution_time", 0),
                memory_usage=result_dict.get("memory_usage", 0),
                timeout=False,
            )


class AutomatedTestRunner:
    """
    Service for running automated tests against student submissions.

    This class integrates with the Django models to:
    1. Load test cases for a given task
    2. Execute student code against each test case
    3. Evaluate results and calculate scores
    4. Update submission records with results
    """

    def __init__(self):
        self.executor = SecureCodeExecutor()

    def _run_single_test(self, student_code: str, test_case) -> TestResult:
        """
        Run student code against a single test case.

        Args:
            student_code: The student's submitted code
            test_case: TestCase model instance

        Returns:
            TestResult object
        """
        try:
            # Create custom timeout for this test case
            executor = SecureCodeExecutor(
                timeout_seconds=test_case.timeout_seconds, memory_limit_mb=128
            )

            # Combine student code with test code
            combined_code = f"""
{student_code}

# Test case execution
{test_case.test_code}
"""

            # Execute the combined code
            result = executor.execute_code(combined_code, test_case.input_data)

            # Check if the test passed based on expected output
            if result.passed and test_case.expected_output:
                # Simple string comparison for now
                # You might want to implement more sophisticated comparison logic
                actual_output = result.output.strip()
                expected_output = test_case.expected_output.strip()

                if actual_output == expected_output:
                    result.passed = True
                else:
                    result.passed = False
                    result.error = f"Expected: {expected_output}, Got: {actual_output}"

            return result

        except Exception as e:
            return TestResult(
                passed=False,
                output="",
                error=f"Test execution error: {str(e)}",
                execution_time=0,
                memory_usage=0,
                timeout=False,
            )

    def run_submission_tests(self, submission) -> SubmissionTestResults:
        """
        Run all test cases for a homework submission.

        Args:
            submission: HomeworkSubmission model instance

        Returns:
            SubmissionTestResults object with complete test results
        """
        from apps.submissions.models import TestCase

        # Get all test cases for this task
        test_cases = TestCase.objects.filter(task=submission.task).order_by("id")

        if not test_cases.exists():
            return SubmissionTestResults(
                total_tests=0,
                passed_tests=0,
                test_results=[],
                overall_execution_time=0.0,
                max_memory_usage=0,
                success_rate=0.0,
            )

        test_results = []
        total_execution_time = 0.0
        max_memory_usage = 0
        passed_count = 0

        # Run each test case
        for test_case in test_cases:
            result = self._run_single_test(submission.code_text, test_case)
            test_results.append(result)

            if result.passed:
                passed_count += 1

            total_execution_time += result.execution_time
            max_memory_usage = max(max_memory_usage, result.memory_usage)

        total_tests = len(test_results)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0

        return SubmissionTestResults(
            total_tests=total_tests,
            passed_tests=passed_count,
            test_results=test_results,
            overall_execution_time=total_execution_time,
            max_memory_usage=max_memory_usage,
            success_rate=success_rate,
        )

    def evaluate_and_update_submission(self, submission) -> SubmissionTestResults:
        """
        Run tests for a submission and update the submission record with results.

        Args:
            submission: HomeworkSubmission model instance

        Returns:
            SubmissionTestResults object
        """
        # Run the tests
        results = self.run_submission_tests(submission)

        # Update the submission with results
        submission.passed_tests = results.passed_tests
        submission.total_tests = results.total_tests
        submission.execution_time = results.overall_execution_time
        submission.memory_usage = results.max_memory_usage
        submission.save()

        return results
