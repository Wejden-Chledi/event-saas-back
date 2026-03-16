# apps/events/views/event_views.py

from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from apps.events.models import Evenement, Inscription
from apps.events.serializers import EvenementSerializer, InscriptionSerializer


class EvenementViewSet(viewsets.ModelViewSet):

    queryset = Evenement.objects.all()
    serializer_class = EvenementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # gestionnaire → voit seulement les événements de son organisation
        if hasattr(user, "gestionnaire_profile"):
             return Evenement.objects.filter(createur=user)

        # utilisateur public → voit seulement événements publiés
        return Evenement.objects.filter(statut="publie")

    def perform_create(self, serializer):
        user = self.request.user

        if hasattr(user, "gestionnaire_profile"):
            organisation = user.gestionnaire_profile.organisation

            serializer.save(
                organisation=organisation,
                createur=user
            )
        else:
            raise PermissionDenied(
                "Seul un gestionnaire peut créer un événement."
            )


# ================================
# Participants d'un événement
# ================================
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def participants_event(request, pk):

    evenement = get_object_or_404(Evenement, pk=pk)

    inscriptions = Inscription.objects.filter(
        evenement=evenement
    ).select_related("participant")

    serializer = InscriptionSerializer(inscriptions, many=True)

    return Response(serializer.data)