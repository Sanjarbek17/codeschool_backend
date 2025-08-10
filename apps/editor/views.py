from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import sys
import io
import multiprocessing

# Create your views here.

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
        code = request.data.get('code', '')
        if not code:
            return Response({'error': 'No code provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Use multiprocessing to enforce timeout
        process = multiprocessing.Process(target=execute_code, args=(code,))
        process.start()
        process.join(timeout=5)  # Set timeout to 5 seconds

        if process.is_alive():
            process.terminate()
            return Response({'output': 'Code execution timed out'}, status=status.HTTP_200_OK)

        return Response({'output': execute_code(code)}, status=status.HTTP_200_OK)
