# apps/events/views/public_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.events.models import Evenement
from apps.events.serializers import EvenementSerializer

@api_view(["GET"])
def public_events(request):
    """
    Retourne la liste des événements publics (statut = 'publie') avec détails utiles.
    """
    events = Evenement.objects.filter(statut="publie").order_by("date_debut")
    serializer = EvenementSerializer(events, many=True)

    return Response(serializer.data)