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
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from api.graphql.schema import schema
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import JsonResponse

class AuthenticatedGraphQLView(GraphQLView):
    """
    GraphQL view that requires JWT authentication.
    In development mode, authentication can be bypassed if DEBUG is True.
    """
    def dispatch(self, request, *args, **kwargs):
        # In development, allow access to GraphiQL without authentication
        if settings.DEBUG and request.method == 'GET':
            return super().dispatch(request, *args, **kwargs)
        
        # For all other requests (including POST queries), require authentication
        auth = JWTAuthentication()
        try:
            user_auth_tuple = auth.authenticate(request)
            if user_auth_tuple is not None:
                request.user, request.auth = user_auth_tuple
            else:
                return JsonResponse(
                    {'errors': [{'message': 'Authentication credentials were not provided.'}]},
                    status=401
                )
        except Exception as e:
            return JsonResponse(
                {'errors': [{'message': f'Authentication failed: {str(e)}'}]},
                status=401
            )
        
        return super().dispatch(request, *args, **kwargs)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', RedirectView.as_view(url='/api/', permanent=True)),
    path('graphql/', csrf_exempt(AuthenticatedGraphQLView.as_view(graphiql=settings.DEBUG, schema=schema))),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
