# apps/users/views/__init__.py

# Auth
from .auth_views import CustomTokenObtainPairView, logout_view

# Profil
from .profile_views import profile_view, update_user_view

# Proprietaire
from .proprietaire_views import register_proprietaire_view

# Participant
from .participant_views import register_participant_view

# Gestionnaire
from .gestionnaire_views import (
    create_gestionnaire_view,
    list_gestionnaires_view,
    update_gestionnaire_view,
    delete_gestionnaire_view
)

# Staff
from .staff_views import (
    create_staff_view,
    list_staff_view,
    update_staff_view,
    delete_staff_view
)