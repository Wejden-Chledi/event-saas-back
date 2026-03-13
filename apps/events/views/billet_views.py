# apps/events/views/billet_views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone

from apps.events.models import Billet
from apps.events.serializers import BilletSerializer


class BilletViewSet(viewsets.ModelViewSet):

    serializer_class = BilletSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Billet.objects.all()

    @action(detail=True, methods=["post"])
    def utiliser(self, request, pk=None):

        billet = self.get_object()

        if not billet.est_utilise:
            billet.est_utilise = True
            billet.date_utilisation = timezone.now()
            billet.save()

            return Response({"success": True})

        return Response({
            "success": False,
            "message": "Billet déjà utilisé"
        })