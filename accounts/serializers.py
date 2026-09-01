from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for public & private user profile details.
    """
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'company_name',
            'phone_number',
            'bio',
            'date_joined',
        ]
        read_only_fields = ['id', 'role', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user as either an Employer or Candidate.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirm your password."
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'password2',
            'first_name',
            'last_name',
            'role',
            'company_name',
            'phone_number',
            'bio',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'role': {'required': True},
            'company_name': {'required': False},
            'phone_number': {'required': False},
            'bio': {'required': False},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # If role is Employer, ensure company_name is provided (or encourage it)
        role = attrs.get('role')
        company_name = attrs.get('company_name')
        if role == User.Role.EMPLOYER and not company_name:
            # Let's provide a friendly fallback or require it
            attrs['company_name'] = attrs.get('username')

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer to inject user role and metadata into token payload and login response.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims inside JWT payload
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['company_name'] = user.company_name or ""
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Include user profile data directly in the JSON response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'company_name': self.user.company_name,
        }
        return data
