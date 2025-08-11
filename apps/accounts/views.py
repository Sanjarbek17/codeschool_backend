from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


class RegisterView(APIView):
    """
    API view for user registration.
    Creates new user account with Teacher or Student profile.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Register a new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            # Get user profile data
            profile_serializer = UserProfileSerializer(user)
            
            return Response({
                'message': 'User registered successfully',
                'user': profile_serializer.data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    """
    API view for user login.
    Authenticates user and returns authentication token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Login user and return token."""
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            # Get user profile data
            profile_serializer = UserProfileSerializer(user)
            
            return Response({
                'message': 'Login successful',
                'user': profile_serializer.data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    """
    API view for user logout.
    Deletes the user's authentication token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Logout user by deleting token."""
        try:
            # Delete the user's token
            token = Token.objects.get(user=request.user)
            token.delete()
            
            logout(request)
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        
        except Token.DoesNotExist:
            return Response({
                'error': 'No active session found'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    API view for user profile management.
    Get and update user profile information.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """Update user profile."""
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):
    """
    API view for changing user password.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Delete old token and create new one for security
            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)
            
            return Response({
                'message': 'Password changed successfully',
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_status(request):
    """
    Simple endpoint to check authentication status.
    """
    return Response({
        'authenticated': True,
        'username': request.user.username,
        'user_id': request.user.id,
        'profile_type': (
            'teacher' if hasattr(request.user, 'teacher_profile') 
            else 'student' if hasattr(request.user, 'student_profile') 
            else 'admin'
        )
    }, status=status.HTTP_200_OK)
