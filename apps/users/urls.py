# apps/users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

urlpatterns = [
    # ---------------------
    # Auth
    # ---------------------
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", logout_view, name="logout"),

    # ---------------------
    # Profil
    # ---------------------
    path("profile/", profile_view, name="profile"),
    path("profile/update/", update_user_view, name="update_profile"),

    # ---------------------
    # Proprietaire
    # ---------------------
    path("proprietaire/register/", register_proprietaire_view, name="register_proprietaire"),

    # ---------------------
    # Participant
    # ---------------------
    path("participant/register/", register_participant_view, name="register_participant"),

    # ---------------------
    # Gestionnaire (CRUD)
    # ---------------------
    path("gestionnaire/create/", create_gestionnaire_view, name="create_gestionnaire"),
    path("gestionnaire/list/", list_gestionnaires_view, name="list_gestionnaires"),
    path("gestionnaire/<int:gestionnaire_id>/update/", update_gestionnaire_view, name="update_gestionnaire"),
    path("gestionnaire/<int:gestionnaire_id>/delete/", delete_gestionnaire_view, name="delete_gestionnaire"),

    # ---------------------
    # Staff (CRUD)
    # ---------------------
    path("staff/create/", create_staff_view, name="create_staff"),
    path("staff/list/", list_staff_view, name="list_staff"),
    path("staff/<int:staff_id>/update/", update_staff_view, name="update_staff"),
    path("staff/<int:staff_id>/delete/", delete_staff_view, name="delete_staff"),
]