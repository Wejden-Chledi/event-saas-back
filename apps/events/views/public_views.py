# apps/events/views/public_views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.events.models import Evenement

@api_view(["GET"])
def public_events(request):
    """
    Retourne la liste des événements publics
    """
    events = Evenement.objects.filter(statut="publie")

    data = [
        {
            "id": e.id,
            "titre": e.titre,
            "description": e.description,
            "lieu": e.lieu,
            "date_debut": e.date_debut.isoformat(),  # convertir en string ISO
            "date_fin": e.date_fin.isoformat(),
            "capaciteMax": e.capacite_max,
            "prix": float(e.prix),
            "statut": e.statut,
        }
        for e in events
    ]

    return Response(data)