# apps/events/views/public_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.events.models import Evenement
from apps.events.serializers import EvenementSerializer
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

@api_view(["GET"])
@permission_classes([AllowAny])
def public_events(request):
    """
    Retourne la liste des événements publics (statut = 'publie') avec détails utiles.
    """
    events = Evenement.objects.filter(statut="publie").order_by("date_debut")
    serializer = EvenementSerializer(events, many=True)

    return Response(serializer.data)



@api_view(["GET"])
@permission_classes([AllowAny])
def public_event_detail(request, evenement_id):
    """
    Retourne les détails d'un événement spécifique sans authentification.
    """
    try:
        # On ne récupère que si l'événement est publié
        event = Evenement.objects.get(id=evenement_id, statut="publie")
        serializer = EvenementSerializer(event)
        return Response(serializer.data)
    except Evenement.DoesNotExist:
        return Response({"error": "Événement non trouvé ou non publié"}, status=404)