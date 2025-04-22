import json
import subprocess
import time
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import sys
import io
import multiprocessing

# Create your views here.

# In-memory rate limit store: {ip: last_request_time}
RATE_LIMIT_STORE = {}
RATE_LIMIT_SECONDS = 2  # adjust as needed

# Blocked keywords (basic protection)
DANGEROUS_KEYWORDS = [
    'import os', 'import subprocess', 'open(', '__import__',
    'eval(', 'exec(', 'import sys', 'from os', 'from sys',
]

def execute_code(code):
    # Redirect stdout to capture print statements
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    try:
        exec(code, {})
        return new_stdout.getvalue()
    except Exception as e:
        return str(e)
    finally:
        sys.stdout = old_stdout

class ExecuteCodeView(APIView):
    def post(self, request, *args, **kwargs):
        ip = request.META.get('REMOTE_ADDR', '')
        now = time.time()

        # Simple rate limiting
        if ip in RATE_LIMIT_STORE and now - RATE_LIMIT_STORE[ip] < RATE_LIMIT_SECONDS:
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)

        RATE_LIMIT_STORE[ip] = now

        try:
            data = json.loads(request.body)
            code = data.get('code', '')

            if not code.strip():
                return JsonResponse({'error': 'Empty code received'}, status=400)

            # Check for unsafe keywords
            for keyword in DANGEROUS_KEYWORDS:
                if keyword in code:
                    return JsonResponse({'error': f'Use of \"{keyword}\" is not allowed'}, status=403)

            # Run the code inside the Docker container
            result = subprocess.run(
                ['docker', 'exec', 'my-python-runner', 'python', '-c', code],
                capture_output=True, text=True, timeout=5
            )

            return JsonResponse({
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })

        except subprocess.TimeoutExpired:
            return JsonResponse({'error': 'Execution timed out'}, status=408)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)