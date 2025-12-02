from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import app_view

schema_view = get_schema_view(
   openapi.Info(
      title="Django Subscriptions API",
      default_version='v1',
      description="API docs",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('swagger(<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("subscriptions/", include("subscriptions.urls")),
    path("billing/", include("billing.urls")),
    path("firebase/", include("accounts_firebase.urls")),
    path('templates/', app_view, name='app'),
]
