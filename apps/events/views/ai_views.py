# apps/events/views/ai_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_event_description(request):
    logger.info("⚡ generate_event_description appelé")
    logger.info("Utilisateur connecté: %s", request.user)
    logger.info("Données reçues: %s", request.data)

    if not request.data.get("titre"):
        logger.warning("Titre manquant dans la requête")
        return Response({"error": "Titre requis"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from ..ai_service import generate_event_description as gen_desc
        description = gen_desc(request.data["titre"])
        logger.info("Description générée: %s", description[:50] + "...")
        return Response({"description": description})
    except Exception as e:
        logger.exception("Erreur lors de la génération de la description IA")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)