# apps/events/views/billet_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404

from apps.events.models import Billet
from apps.events.serializers import BilletSerializer


class BilletViewSet(viewsets.ModelViewSet):

    serializer_class = BilletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retourne uniquement les billets de l'utilisateur connecté
        """
        user = self.request.user

        return Billet.objects.filter(
            inscription__participant=user
        ).select_related(
            "inscription",
            "inscription__evenement"
        )

    # =============================
    # Utiliser billet (scan entrée)
    # =============================
    @action(detail=True, methods=["post"])
    def utiliser(self, request, pk=None):

        billet = self.get_object()

        if billet.utilise:
            return Response(
                {
                    "success": False,
                    "message": "Billet déjà utilisé"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        billet.utilise = True
        billet.date_utilisation = timezone.now()
        billet.save()

        return Response({
            "success": True,
            "message": "Billet validé avec succès"
        })

    # =============================
    # Vérifier billet via QR
    # =============================
    @action(detail=False, methods=["post"])
    def verifier_qr(self, request):

        billet_id = request.data.get("billet_id")

        if not billet_id:
            return Response(
                {"success": False, "message": "billet_id requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        billet = get_object_or_404(
            Billet.objects.select_related(
                "inscription",
                "inscription__evenement",
                "inscription__participant"
            ),
            id=billet_id
        )

        if billet.utilise:
            return Response({
                "success": False,
                "message": "Billet déjà utilisé"
            })

        serializer = BilletSerializer(billet, context={"request": request})

        return Response({
            "success": True,
            "billet": serializer.data
        })