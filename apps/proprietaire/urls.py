# apps/proprietaire/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    InformationOrganisationViewSet,
    GestionnaireViewSet,
    mon_organisation_complete,
    modifier_organisation_base,
    changer_abonnement,
    mes_demandes_abonnement
)

router = DefaultRouter()
router.register(r'informations', InformationOrganisationViewSet, basename='proprietaire-informations')
router.register(r'gestionnaires', GestionnaireViewSet, basename='proprietaire-gestionnaires')

urlpatterns = [
    path('', include(router.urls)),
    path('organisation/', mon_organisation_complete, name='organisation-detail'),
    path('organisation/modifier/', modifier_organisation_base, name='organisation-modifier'),
    path('abonnement/changer/', changer_abonnement, name='abonnement-changer'),
    path('abonnement/demandes/', mes_demandes_abonnement, name='abonnement-demandes'),
    
]