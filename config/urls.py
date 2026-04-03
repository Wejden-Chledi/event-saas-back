# config/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

# Endpoint health pour Azure probes
def health(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # APIs
    path("api/users/", include("apps.users.urls")),
    path("api/organisations/", include("apps.organisations.urls")),
    path("api/events/", include("apps.events.urls")),
    path("api/staff/", include("apps.events.staff_urls")),
    path("api/inscriptions/", include("apps.inscriptions.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/assistant/", include("apps.assistant.urls")),


    # Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),

    # Health check pour Azure
    path('health/', health),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)