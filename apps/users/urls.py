# ============================================================================
# Fichier : apps/users/urls.py
#
# Ce fichier définit les routes URL liées à l'application users.
#
# Il regroupe :
#   - l'authentification (login, logout, refresh token)
#   - l'inscription des utilisateurs
#   - la gestion du profil utilisateur
#   - la gestion des gestionnaires et du staff via des ViewSets
# ============================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.auth_views import (
    CustomTokenObtainPairView,
    logout_view
)
from .views.profile_views import (
    profile_view,
    update_user_view
)
from .views.management_views import (
    GestionnaireViewSet,
    StaffViewSet
)
from .views.proprietaire_views import register_proprietaire_view
from .views.participant_views import register_participant_view
from rest_framework_simplejwt.views import TokenRefreshView
router = DefaultRouter()


# Enregistrement du ViewSet Gestionnaire.
#
# Les routes générées seront par exemple :
#
# GET     /gestionnaire/
# POST    /gestionnaire/
# GET     /gestionnaire/{id}/
# PUT     /gestionnaire/{id}/
# DELETE  /gestionnaire/{id}/
router.register(
    r'gestionnaire',
    GestionnaireViewSet,
    basename='gestionnaire'
)


# Enregistrement du ViewSet Staff.
#
# Les routes générées seront :
#
# GET     /staff/
# POST    /staff/
# GET     /staff/{id}/
# PUT     /staff/{id}/
# DELETE  /staff/{id}/
#
# Il contient également l'action personnalisée :
# POST /staff/{id}/assign_event/
router.register(
    r'staff',
    StaffViewSet,
    basename='staff'
)



# ============================================================================
# LISTE DES URLS DE L'APPLICATION
# ============================================================================

urlpatterns = [

    # ------------------------------------------------------------------------
    # AUTHENTIFICATION ET INSCRIPTIONS
    # ------------------------------------------------------------------------

    # Connexion utilisateur avec JWT.
    #
    # Génère :
    # POST /auth/login/
    #
    # Retourne :
    # - access token
    # - refresh token
    path(
        "auth/login/",
        CustomTokenObtainPairView.as_view(),
        name="login"
    ),


    # Déconnexion utilisateur.
    #
    # POST /auth/logout/
    path(
        "auth/logout/",
        logout_view,
        name="logout"
    ),


    # Inscription d'un propriétaire.
    #
    # POST /proprietaire/register/
    path(
        "proprietaire/register/",
        register_proprietaire_view,
        name="register-proprietaire"
    ),


    # Inscription d'un participant.
    #
    # POST /participant/register/
    path(
        "participant/register/",
        register_participant_view,
        name="register-participant"
    ),



    # ------------------------------------------------------------------------
    # GESTION DU PROFIL
    # ------------------------------------------------------------------------

    # Consultation du profil utilisateur connecté.
    #
    # GET /profile/
    path(
        "profile/",
        profile_view,
        name="user-profile"
    ),


    # Modification du profil utilisateur connecté.
    #
    # PUT /profile/update/
    path(
        "profile/update/",
        update_user_view,
        name="user-profile-update"
    ),



    # ------------------------------------------------------------------------
    # ROUTES AUTOMATIQUES DES VIEWSETS
    # ------------------------------------------------------------------------

    # Inclusion des routes générées automatiquement
    # par le DefaultRouter.
    #
    # Ces routes correspondent aux ViewSets :
    #   - GestionnaireViewSet
    #   - StaffViewSet
    path(
        "",
        include(router.urls)
    ),



    # ------------------------------------------------------------------------
    # RAFRAÎCHISSEMENT DU TOKEN JWT
    # ------------------------------------------------------------------------

    # Permet d'obtenir un nouveau token d'accès
    # lorsque l'ancien expire.
    #
    # POST /auth/token/refresh/
    path(
        'auth/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

]