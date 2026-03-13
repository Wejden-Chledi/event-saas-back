# apps/events/views/staff_views.py

from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers

from apps.events.models import Staff, AssignationEvenement, Evenement
from apps.events.serializers import StaffSerializer, StaffCreateSerializer , StaffUpdateSerializer


class StaffViewSet(viewsets.ModelViewSet):

    permission_classes = [permissions.IsAuthenticated]

    # Choisir le serializer selon l'action
    def get_serializer_class(self):
        if self.action == "create":
            return StaffCreateSerializer
        if self.action in ["update", "partial_update"]:
            return StaffUpdateSerializer
        return StaffSerializer


    # Staffs de l'organisation du gestionnaire connecté
    def get_queryset(self):

        user = self.request.user

        try:
            organisation = user.gestionnaire_profile.organisation
        except AttributeError:
            return Staff.objects.none()

        return Staff.objects.filter(organisation=organisation)


    # Création d'un staff
    def perform_create(self, serializer):

        user = self.request.user

        try:
            organisation = user.gestionnaire_profile.organisation
        except AttributeError:
            raise serializers.ValidationError(
                "Impossible de créer un staff : organisation manquante"
            )

        serializer.save(organisation=organisation)


    # =====================================================
    # ASSIGNER UN EVENEMENT A UN STAFF
    # =====================================================
    @action(detail=True, methods=["post"])
    def assigner_evenement(self, request, pk=None):

        staff = self.get_object()
        evenement_id = request.data.get("evenement_id")

        if not evenement_id:
            return Response(
                {"error": "evenement_id manquant"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            organisation = request.user.gestionnaire_profile.organisation
        except AttributeError:
            return Response(
                {"error": "Organisation introuvable"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            evenement = Evenement.objects.get(
                id=evenement_id,
                organisation=organisation
            )
        except Evenement.DoesNotExist:
            return Response(
                {"error": "Evenement introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )

        # créer ou récupérer assignation
        assignation, created = AssignationEvenement.objects.get_or_create(
            staff=staff,
            evenement=evenement
        )

        return Response({
            "success": True,
            "assignation_id": assignation.id,
            "created": created
        }, status=status.HTTP_200_OK)