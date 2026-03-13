from .event_views import EvenementViewSet , participants_event
from .public_views import public_events

from .participant_views import (
    register_event_participant,
    mes_inscriptions,
    mon_billet,
    telecharger_billet_pdf
)

from .staff_views import StaffViewSet
from .billet_views import BilletViewSet
from .ai_views import generate_event_description
from .debug_views import debug_user_profile