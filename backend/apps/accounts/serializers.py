"""
Serializers for the Accounts application.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.accounts.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer responsible for user registration.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User

        fields = (
            "email",
            "first_name",
            "last_name",
            "password",
        )

    def validate_email(self, value):
        """
        Ensure the email address is unique.
        """

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def create(self, validated_data):
        """
        Create and return a new user.
        """

        password = validated_data.pop("password")

        return User.objects.create_user(
            password=password,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    """
    Serializer responsible for authenticating users.
    """

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        """
        Validate user credentials.
        """

        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            username=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                {
                    "detail": "Invalid email or password."
                }
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {
                    "detail": "This account is inactive."
                }
            )

        attrs["user"] = user

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for authenticated users.
    """

    class Meta:
        model = User

        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
        )

        read_only_fields = fields