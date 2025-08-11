from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
from .models import User, Teacher, Student


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles password confirmation and validation.
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    user_type = serializers.ChoiceField(
        choices=[('teacher', 'Teacher'), ('student', 'Student')],
        write_only=True
    )
    
    # Profile fields
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20)
    parents_phone_number = serializers.CharField(
        max_length=20, 
        required=False, 
        allow_blank=True,
        help_text="Required for students only"
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm', 
            'user_type', 'first_name', 'last_name', 'phone_number', 
            'parents_phone_number'
        )

    def validate(self, attrs):
        """Validate password confirmation and user type specific fields."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password and password confirmation don't match.")
        
        # Validate student-specific fields
        if attrs['user_type'] == 'student' and not attrs.get('parents_phone_number'):
            raise serializers.ValidationError(
                "Parent's phone number is required for students."
            )
        
        return attrs

    def create(self, validated_data):
        """Create user and associated profile (Teacher or Student)."""
        # Remove non-user fields
        password_confirm = validated_data.pop('password_confirm')
        user_type = validated_data.pop('user_type')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        phone_number = validated_data.pop('phone_number')
        parents_phone_number = validated_data.pop('parents_phone_number', '')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create profile based on user type
        if user_type == 'teacher':
            Teacher.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number
            )
        elif user_type == 'student':
            Student.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                parents_phone_number=parents_phone_number
            )
        
        # Create authentication token
        Token.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Authenticates user and returns token.
    """
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        """Authenticate user credentials."""
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.'
                )

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "username" and "password".'
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    Includes profile data from Teacher or Student models.
    """
    profile_type = serializers.SerializerMethodField()
    profile_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_joined', 'profile_type', 'profile_data'
        )
        read_only_fields = ('id', 'username', 'date_joined')

    def get_profile_type(self, obj):
        """Determine if user is a teacher or student."""
        if hasattr(obj, 'teacher_profile'):
            return 'teacher'
        elif hasattr(obj, 'student_profile'):
            return 'student'
        return None

    def get_profile_data(self, obj):
        """Get profile data based on user type."""
        if hasattr(obj, 'teacher_profile'):
            return TeacherProfileSerializer(obj.teacher_profile).data
        elif hasattr(obj, 'student_profile'):
            return StudentProfileSerializer(obj.student_profile).data
        return None


class TeacherProfileSerializer(serializers.ModelSerializer):
    """Serializer for Teacher profile data."""
    
    class Meta:
        model = Teacher
        fields = (
            'first_name', 'last_name', 'phone_number', 
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for Student profile data."""
    
    class Meta:
        model = Student
        fields = (
            'first_name', 'last_name', 'phone_number', 
            'parents_phone_number', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        """Validate password change request."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                "New password and confirmation don't match."
            )
        return attrs

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
