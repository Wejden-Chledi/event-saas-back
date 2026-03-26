# apps/organisations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.organisation_views import OrganisationViewSet
from .views.abonnement_views import get_abonnement_view, update_abonnement_view

router = DefaultRouter()
# Le préfixe vide '' signifie que les routes seront /api/organisations/me/, etc.
router.register(r'', OrganisationViewSet, basename='organisation')

urlpatterns = [
    # 1. Routes manuelles d'abord
    path("abonnement/", get_abonnement_view, name='get_abonnement'),
    path("abonnement/update/", update_abonnement_view, name='update_abonnement'),
    
    # 2. Routes automatiques du ViewSet (stats, me, etc.)
    path("", include(router.urls)),
]