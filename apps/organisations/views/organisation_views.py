# apps/organisations/views/organisation_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsProprietaire, IsGestionnaire
from ..models import Organisation
from ..serializers import (
    OrganisationSerializer,
    OrganisationCompleteSerializer,
    OrganisationCreateSerializer
)


class OrganisationViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'me', 'stats']:
            return [IsAuthenticated(), (IsProprietaire | IsGestionnaire)()]
        return [IsAuthenticated(), IsProprietaire()]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Organisation.objects.none()

        if user.role == "proprietaire":
            return Organisation.objects.filter(proprietaire=user)

        if hasattr(user, "organisation") and user.organisation:
            return Organisation.objects.filter(id=user.organisation.id)

        return Organisation.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return OrganisationCreateSerializer
        if self.action in ["retrieve", "me"]:
            return OrganisationCompleteSerializer
        return OrganisationSerializer

    # =========================
    # CREATE FIXED
    # =========================
    def perform_create(self, serializer):
        serializer.save(proprietaire=self.request.user)

    # =========================
    # ME (CORRIGÉ POUR GESTIONNAIRE)
    # =========================
    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        user = request.user

        # 🛠️ CORRECTION : On récupère l'organisation selon le rôle de l'utilisateur connecté
        if user.role == "proprietaire":
            organisation = Organisation.objects.filter(proprietaire=user).first()
        else:
            # Si c'est un gestionnaire, on prend l'organisation qui lui est associée
            organisation = getattr(user, "organisation", None)

        if not organisation:
            return Response(
                {"error": "Aucune organisation associée à votre compte"},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method in ['PATCH', 'PUT']:
            if user.role != "proprietaire":
                return Response(
                    {"error": "Seul le propriétaire peut modifier l'organisation"},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = OrganisationSerializer(
                organisation,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = OrganisationCompleteSerializer(organisation)
        return Response(serializer.data)

    # =========================
    # STATS (CORRIGÉ POUR GESTIONNAIRE)
    # =========================
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user

        # 🛠️ CORRECTION : Même logique pour éviter le crash des stats
        if user.role == "proprietaire":
            org = Organisation.objects.filter(proprietaire=user).first()
        else:
            org = getattr(user, "organisation", None)

        if not org:
            return Response([])

        return Response([
            {"label": "Événements", "value": 0, "color": "blue"},
            {
                "label": "Gestionnaires",
                # Utilisation de la relation inverse (utilisateurs ou utilisateur_set selon ton modèle)
                "value": org.utilisateurs.filter(role='gestionnaire').count() if hasattr(org, 'utilisateurs') else 0,
                "color": "green"
            },
            {"label": "Inscriptions", "value": 0, "color": "purple"},
        ])