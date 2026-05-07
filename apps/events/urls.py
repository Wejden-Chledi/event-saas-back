from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvenementViewSet

router = DefaultRouter()
router.register(r'', EvenementViewSet, basename='evenement')

urlpatterns = [
    # 1️⃣ router en premier
    path('', include(router.urls)),

    # 2️⃣ staff MUST be explicit path (PAS include root '')
    path('assigned/', include('apps.events.staff_urls')),
]