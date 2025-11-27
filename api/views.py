from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user account using email.

    Request body:
    {
        "email": "string",
        "password": "string"
    }
    """
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "email and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Use email as username (Django requires username field)
        user = User.objects.create_user(username=email, email=email, password=password)

        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "User created successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to create user: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Login using email and obtain JWT tokens.

    Request body:
    {
        "email": "string",
        "password": "string"
    }
    """
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "email and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Authenticate using email as username
    user = authenticate(username=email, password=password)

    if user is None:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {"error": "User account is disabled"}, status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "user": {
                "id": user.id,
                "email": user.email,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile (requires authentication).

    Headers:
    Authorization: Bearer <access_token>
    """
    user = request.user

    return Response(
        {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined,
        },
        status=status.HTTP_200_OK,
    )
