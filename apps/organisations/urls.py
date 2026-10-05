# ============================================================================
# Fichier : apps/organisations/urls.py
#
# Ce fichier définit les routes URL liées à l'application organisations.
#
# Il contient :
#
#   - Les routes manuelles pour la gestion des abonnements
#   - Les routes automatiques générées par le ViewSet OrganisationViewSet
#
# Le DefaultRouter permet de générer automatiquement
# les URLs CRUD et les actions personnalisées du ViewSet.
# ============================================================================



# ==============================
# IMPORTATION DES MODULES DJANGO
# ==============================


# path permet de définir une route URL.
#
# include permet d'intégrer les URLs générées
# par un autre module.
from django.urls import path, include




# ==============================
# IMPORTATION DU ROUTER DRF
# ==============================


# DefaultRouter permet de générer automatiquement
# les routes associées aux ViewSets Django REST Framework.
#
# Il crée automatiquement les routes :
#
# GET       /organisations/
# POST      /organisations/
# GET/id    /organisations/{id}/
# PUT       /organisations/{id}/
# PATCH     /organisations/{id}/
# DELETE    /organisations/{id}/
from rest_framework.routers import DefaultRouter




# ==============================
# IMPORTATION DES VUES
# ==============================


# ViewSet principal permettant la gestion
# des organisations.
from .views.organisation_views import OrganisationViewSet



# Vues permettant :
#
# - consulter l'abonnement actuel
# - modifier l'abonnement
from .views.abonnement_views import (
    get_abonnement_view,
    update_abonnement_view
)




# ============================================================================
# CONFIGURATION DU ROUTER
# ============================================================================


# Création du routeur automatique DRF.
#
# Le routeur va générer automatiquement
# les URLs associées au OrganisationViewSet.
router = DefaultRouter()



# Enregistrement du ViewSet OrganisationViewSet.
#
# Le préfixe vide signifie que les routes
# commenceront directement après le chemin
# défini dans urls.py principal.
#
# Exemple :
#
# /api/organisations/me/
# /api/organisations/stats/
#
# et non :
#
# /api/organisations/organisation/me/
#
router.register(
    r'',
    OrganisationViewSet,
    basename='organisation'
)




# ============================================================================
# DEFINITION DES URLS
# ============================================================================


urlpatterns = [



    # ------------------------------------------------------------------------
    # ROUTES MANUELLES : ABONNEMENT
    # ------------------------------------------------------------------------
    #
    # Ces routes sont déclarées avant les routes
    # automatiques du router afin d'éviter
    # les conflits de résolution d'URL.
    # ------------------------------------------------------------------------



    # Consultation de l'abonnement actuel.
    #
    # Méthode :
    #       GET
    #
    # URL :
    #       /api/organisations/abonnement/
    path(
        "abonnement/",
        get_abonnement_view,
        name='get_abonnement'
    ),



    # Modification de l'abonnement.
    #
    # Méthode :
    #       PUT
    #
    # URL :
    #       /api/organisations/abonnement/update/
    path(
        "abonnement/update/",
        update_abonnement_view,
        name='update_abonnement'
    ),




    # ------------------------------------------------------------------------
    # ROUTES AUTOMATIQUES DU VIEWSET
    # ------------------------------------------------------------------------
    #
    # Inclusion des routes générées automatiquement
    # par DefaultRouter.
    #
    # Ces routes correspondent aux actions :
    #
    # CRUD :
    #   - list
    #   - retrieve
    #   - create
    #   - update
    #   - delete
    #
    # Actions personnalisées :
    #   - /me/
    #   - /stats/
    # ------------------------------------------------------------------------


    path(
        "",
        include(router.urls)
    ),

]