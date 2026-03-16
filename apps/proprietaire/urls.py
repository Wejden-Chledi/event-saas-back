# apps/proprietaire/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    InformationOrganisationViewSet,
    GestionnaireViewSet,
    mon_organisation_complete,
    modifier_organisation_base,
    changer_abonnement,
    mes_demandes_abonnement,
)

# Router DRF
router = DefaultRouter()

router.register(
    r'informations',
    InformationOrganisationViewSet,
    basename='proprietaire-informations'
)

router.register(
    r'gestionnaires',
    GestionnaireViewSet,
    basename='proprietaire-gestionnaires'
)

urlpatterns = [
    # routes ViewSets
    path('', include(router.urls)),

    # organisation
    path(
        'organisation/',
        mon_organisation_complete,
        name='proprietaire-organisation'
    ),

    path(
        'organisation/modifier/',
        modifier_organisation_base,
        name='proprietaire-organisation-modifier'
    ),

    # abonnement
    path(
        'abonnement/changer/',
        changer_abonnement,
        name='proprietaire-abonnement-changer'
    ),

    path(
        'abonnement/demandes/',
        mes_demandes_abonnement,
        name='proprietaire-abonnement-demandes'
    ),

]