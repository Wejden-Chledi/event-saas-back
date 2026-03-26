# apps/users/views/__init__.py

# Auth
from .auth_views import CustomTokenObtainPairView, logout_view

# Profil
from .profile_views import profile_view, update_user_view

# Proprietaire
from .proprietaire_views import register_proprietaire_view

# Participant
from .participant_views import register_participant_view

# management(staff+gestionnaire)
from .management_views import (
    BaseUserViewSet,
    GestionnaireViewSet,
    StaffViewSet
)

