from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import sys
import io

# Create your views here.

class ExecuteCodeView(APIView):
    def post(self, request, *args, **kwargs):
        code = request.data.get('code', '')
        if not code:

            return Response({'error': 'No code provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Redirect stdout to capture print statements
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        try:
            exec(code, {})
            output = new_stdout.getvalue()
        except Exception as e:
            output = str(e)
        finally:
            # Reset stdout
            sys.stdout = old_stdout

        return Response({'output': output}, status=status.HTTP_200_OK)
