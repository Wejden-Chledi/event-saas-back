# apps/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.auth_views import CustomTokenObtainPairView, logout_view
from .views.profile_views import profile_view, update_user_view
from .views.management_views import GestionnaireViewSet, StaffViewSet
from .views.proprietaire_views import register_proprietaire_view
from .views.participant_views import register_participant_view

# Le router génère automatiquement les URLs : list, create, retrieve, update, delete
router = DefaultRouter()
router.register(r'gestionnaire', GestionnaireViewSet, basename='gestionnaire')
router.register(r'staff', StaffViewSet, basename='staff')

urlpatterns = [
    # Auth & Inscriptions
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("auth/logout/", logout_view, name="logout"),
    path("proprietaire/register/", register_proprietaire_view),
    path("participant/register/", register_participant_view),

    # Profil
    path("profile/", profile_view),
    path("profile/update/", update_user_view),

    # Inclusion des routes automatiques
    path("", include(router.urls)),
]