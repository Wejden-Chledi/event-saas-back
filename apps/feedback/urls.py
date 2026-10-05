# ============================================================================
# Fichier : apps/feedback/urls.py
#
# Ce fichier contient la configuration des routes API du module Feedback.
#
# Il définit les endpoints liés :
#
#   - Aux avis des participants :
#       * Création et consultation des feedbacks.
#       * Analyse globale de l'organisation.
#
#   - Aux rapports IA :
#       * Consultation des rapports générés.
#       * Génération d'analyses intelligentes pour les événements.
#
# Les routes sont générées automatiquement grâce au DefaultRouter de Django REST
# Framework.
#
# Endpoints principaux :
#
#   Feedback :
#       /api/feedback/avis/
#       /api/feedback/avis/analyse_globale/
#
#   Rapports IA :
#       /api/feedback/rapports-ia/
#       /api/feedback/rapports-ia/{id}/generer/
#
# ============================================================================


from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import (
    FeedbackViewSet,
    RapportIAViewSet
)



# ============================================================================
# Configuration du routeur REST Framework
#
# Le router permet de générer automatiquement les URLs CRUD
# associées aux ViewSets.
# ============================================================================

router = DefaultRouter()



# ----------------------------------------------------------------------------
# Routes Feedback
#
# Génère automatiquement :
#
#   GET      /avis/
#   POST     /avis/
#   GET      /avis/{id}/
#   PUT      /avis/{id}/
#   DELETE   /avis/{id}/
#
# Actions personnalisées :
#
#   GET /avis/analyse_globale/
#
# ----------------------------------------------------------------------------

router.register(
    r'avis',
    FeedbackViewSet,
    basename='feedback'
)



# ----------------------------------------------------------------------------
# Routes Rapports IA
#
# Génère automatiquement :
#
#   GET /rapports-ia/
#   GET /rapports-ia/{id}/
#
# Action personnalisée :
#
#   POST /rapports-ia/{id}/generer/
#
# ----------------------------------------------------------------------------

router.register(
    r'rapports-ia',
    RapportIAViewSet,
    basename='rapport-ia'
)



# ============================================================================
# Inclusion des routes générées par le router
#
# Toutes les URLs du module Feedback seront accessibles sous le préfixe
# défini dans le fichier urls.py principal du projet.
# ============================================================================

urlpatterns = [

    path(
        '',
        include(router.urls)
    ),

]