from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Group
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    GroupSerializer,
    GroupListSerializer,
    GroupCreateUpdateSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    """
    User Registration API

    Creates a new user account with either Teacher or Student profile.
    Returns user data and authentication token upon successful registration.
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user account (Teacher or Student)",
        operation_summary="User Registration",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                examples={
                    "application/json": {
                        "message": "User registered successfully",
                        "user": {
                            "id": 1,
                            "username": "teacher1",
                            "profile_type": "teacher",
                            "profile_data": {
                                "first_name": "John",
                                "last_name": "Doe",
                                "phone_number": "+1234567890",
                            },
                        },
                        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                    }
                },
            ),
            400: openapi.Response(
                description="Validation errors",
                examples={
                    "application/json": {
                        "username": ["This field is required."],
                        "password": ["This password is too short."],
                    }
                },
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        """Register a new user."""
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)

            # Get user profile data
            profile_serializer = UserProfileSerializer(user)

            return Response(
                {
                    "message": "User registered successfully",
                    "user": profile_serializer.data,
                    "token": token.key,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    User Login API

    Authenticates user credentials and returns authentication token.
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Authenticate user credentials and get access token",
        operation_summary="User Login",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "message": "Login successful",
                        "user": {
                            "id": 1,
                            "username": "teacher1",
                            "email": "teacher@example.com",
                            "profile_type": "teacher",
                            "profile_data": {
                                "first_name": "John",
                                "last_name": "Doe",
                                "phone_number": "+1234567890",
                            },
                        },
                        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                    }
                },
            ),
            400: openapi.Response(
                description="Invalid credentials",
                examples={
                    "application/json": {
                        "non_field_errors": ["Invalid username or password."]
                    }
                },
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        """Login user and return token."""
        serializer = UserLoginSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)

            # Get or create token
            token, created = Token.objects.get_or_create(user=user)

            # Get user profile data
            profile_serializer = UserProfileSerializer(user)

            return Response(
                {
                    "message": "Login successful",
                    "user": profile_serializer.data,
                    "token": token.key,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    User Logout API

    Deletes the user's authentication token and logs them out.
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logout user by deleting authentication token",
        operation_summary="User Logout",
        responses={
            200: openapi.Response(
                description="Logout successful",
                examples={"application/json": {"message": "Logout successful"}},
            ),
            400: openapi.Response(
                description="No active session found",
                examples={"application/json": {"error": "No active session found"}},
            ),
            401: "Unauthorized - Invalid or missing token",
        },
        tags=["Authentication"],
        security=[{"Token": []}],
    )
    def post(self, request):
        """Logout user by deleting token."""
        try:
            # Delete the user's token
            token = Token.objects.get(user=request.user)
            token.delete()

            logout(request)

            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

        except Token.DoesNotExist:
            return Response(
                {"error": "No active session found"}, status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(APIView):
    """
    User Profile Management API

    Get and update user profile information for authenticated users.
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get current user profile information",
        operation_summary="Get User Profile",
        responses={
            200: openapi.Response(
                description="User profile data",
                examples={
                    "application/json": {
                        "id": 1,
                        "username": "teacher1",
                        "email": "teacher@example.com",
                        "profile_type": "teacher",
                        "profile_data": {
                            "first_name": "John",
                            "last_name": "Doe",
                            "phone_number": "+1234567890",
                            "created_at": "2025-08-11T00:00:00Z",
                        },
                    }
                },
            ),
            401: "Unauthorized - Invalid or missing token",
        },
        tags=["Authentication"],
        security=[{"Token": []}],
    )
    def get(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update current user profile information",
        operation_summary="Update User Profile",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                examples={
                    "application/json": {
                        "message": "Profile updated successfully",
                        "user": {
                            "id": 1,
                            "username": "teacher1",
                            "email": "newemail@example.com",
                            "profile_type": "teacher",
                            "profile_data": {
                                "first_name": "Updated John",
                                "last_name": "Updated Doe",
                                "phone_number": "+1234567891",
                            },
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="Validation errors",
                examples={
                    "application/json": {"email": ["Enter a valid email address."]}
                },
            ),
            401: "Unauthorized - Invalid or missing token",
        },
        tags=["Authentication"],
        security=[{"Token": []}],
    )
    def put(self, request):
        """Update user profile."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Profile updated successfully", "user": serializer.data},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API view for changing user password.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            # Delete old token and create new one for security
            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)

            return Response(
                {"message": "Password changed successfully", "token": token.key},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_status(request):
    """
    Simple endpoint to check authentication status.
    """
    return Response(
        {
            "authenticated": True,
            "username": request.user.username,
            "user_id": request.user.id,
            "profile_type": (
                "teacher"
                if hasattr(request.user, "teacher_profile")
                else "student" if hasattr(request.user, "student_profile") else "admin"
            ),
        },
        status=status.HTTP_200_OK,
    )


class GroupListCreateView(ListCreateAPIView):
    """
    Group List and Create API

    GET: List all groups with teacher and student counts
    POST: Create a new group
    """

    queryset = Group.objects.all().prefetch_related("teachers", "students")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GroupCreateUpdateSerializer
        return GroupListSerializer

    @swagger_auto_schema(
        operation_description="List all groups",
        operation_summary="Get Groups List",
        tags=["Group Management"],
        responses={200: GroupListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new group",
        operation_summary="Create Group",
        tags=["Group Management"],
        request_body=GroupCreateUpdateSerializer,
        responses={201: GroupSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class GroupDetailView(RetrieveUpdateDestroyAPIView):
    """
    Group Detail API

    GET: Retrieve detailed group information
    PUT/PATCH: Update group information
    DELETE: Delete group
    """

    queryset = Group.objects.all().prefetch_related("teachers", "students")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return GroupCreateUpdateSerializer
        return GroupSerializer

    @swagger_auto_schema(
        operation_description="Get detailed group information",
        operation_summary="Get Group Detail",
        tags=["Group Management"],
        responses={200: GroupSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update group information",
        operation_summary="Update Group",
        tags=["Group Management"],
        request_body=GroupCreateUpdateSerializer,
        responses={200: GroupSerializer},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update group information",
        operation_summary="Partially Update Group",
        tags=["Group Management"],
        request_body=GroupCreateUpdateSerializer,
        responses={200: GroupSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete group",
        operation_summary="Delete Group",
        tags=["Group Management"],
        responses={204: "Group deleted successfully"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
