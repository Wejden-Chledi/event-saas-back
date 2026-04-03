# apps/events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvenementViewSet

router = DefaultRouter()
# On change r'' par r'all' ou on laisse vide mais on change l'ordre
router.register(r'', EvenementViewSet, basename='evenement')

urlpatterns = [
    path('', include(router.urls)),
]