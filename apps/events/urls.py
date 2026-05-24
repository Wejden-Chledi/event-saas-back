# apps/events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvenementViewSet

router = DefaultRouter()
router.register(r'', EvenementViewSet, basename='evenement')

urlpatterns = [
    # On garde uniquement le router principal pour les événements classiques
    path('', include(router.urls)),
    
    # ❌ SUPPRIME OU RECOUVRE CETTE LIGNE qui sème la confusion :
    # path('assigned/', include('apps.events.staff_urls')),
]