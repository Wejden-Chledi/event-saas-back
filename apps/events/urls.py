# apps/events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvenementViewSet

# Le router génère automatiquement les routes :
# GET /             -> list
# POST /            -> create
# GET /{id}/        -> retrieve
# PUT /{id}/        -> update
# DELETE /{id}/     -> destroy
# POST /generate_ai_desc/ -> action personnalisée
router = DefaultRouter()
router.register(r'', EvenementViewSet, basename='evenement')

urlpatterns = [
    # Toutes les routes (Public, Gestionnaire, IA) sont regroupées sous le ViewSet
    path('', include(router.urls)),
]