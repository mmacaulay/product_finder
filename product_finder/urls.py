"""
URL configuration for product_finder project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from api.graphql.schema import schema
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from api.firebase_auth import verify_token


class AuthenticatedGraphQLView(GraphQLView):
    """
    GraphQL view that requires Firebase Auth authentication.
    In development mode (DEBUG=True), authentication is bypassed completely.
    """

    def dispatch(self, request, *args, **kwargs):
        # In development, bypass authentication entirely
        if settings.DEBUG:
            return super().dispatch(request, *args, **kwargs)

        # In production, require Firebase Auth token
        # Extract token from Authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {
                    "errors": [
                        {"message": "Authentication credentials were not provided."}
                    ]
                },
                status=401,
            )

        token = auth_header.split("Bearer ")[1]
        user_claims = verify_token(token)

        if user_claims is None:
            return JsonResponse(
                {"errors": [{"message": "Invalid or expired token."}]},
                status=401,
            )

        # Attach user claims to request for use in resolvers
        request.firebase_user = user_claims
        return super().dispatch(request, *args, **kwargs)


urlpatterns = [
    path("api/", include("api.urls")),
    path("", RedirectView.as_view(url="/graphql/", permanent=True)),
    path(
        "graphql/",
        csrf_exempt(
            AuthenticatedGraphQLView.as_view(graphiql=settings.DEBUG, schema=schema)
        ),
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
