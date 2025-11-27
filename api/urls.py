from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

urlpatterns = [
    # Authentication endpoints (public - no auth required)
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login, name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # User profile endpoint (requires authentication)
    path("auth/me/", views.user_profile, name="user_profile"),
]
