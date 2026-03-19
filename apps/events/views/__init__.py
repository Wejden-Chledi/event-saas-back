# apps/events/views/__init__.py

# Import des vues principales
from .event_views import (
    create_evenement_view,
    list_evenements_view,
    retrieve_evenement_view,
    update_evenement_view,
    delete_evenement_view,
    assign_staff_view,
    list_staff_assignes_view,
)

from .ai_views import generate_event_description

from .public_views import public_events

# Optionnel : liste __all__ pour faciliter les imports *
__all__ = [
    "create_evenement_view",
    "list_evenements_view",
    "retrieve_evenement_view",
    "update_evenement_view",
    "delete_evenement_view",
    "assign_staff_view",
    "list_staff_assignes_view",
    "generate_event_description",
    "public_events",
]