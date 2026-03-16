# src/apps/proprietaire/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import InformationOrganisation, Gestionnaire, DemandeAbonnement
from .serializers import (
    InformationOrganisationSerializer,
    GestionnaireSerializer,
    GestionnaireCreateSerializer,
    DemandeAbonnementSerializer,
    OrganisationCompleteSerializer,
    ChangerAbonnementSerializer
)
from apps.organisations.models import Organisation


# =====================================================
# Permission propriétaire
# =====================================================
class IsProprietaireOrReadOnly(permissions.BasePermission):
    """Autorise uniquement le propriétaire de l'organisation"""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "organisation"):
            return obj.organisation.proprietaire == request.user
        return getattr(obj, 'proprietaire', None) == request.user


# =====================================================
# Informations organisation
# =====================================================
class InformationOrganisationViewSet(viewsets.ModelViewSet):
    serializer_class = InformationOrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InformationOrganisation.objects.filter(
            organisation__proprietaire=self.request.user
        )

    def perform_create(self, serializer):
        organisation = get_object_or_404(Organisation, proprietaire=self.request.user)
        serializer.save(organisation=organisation)


# =====================================================
# Gestionnaires
# =====================================================
class GestionnaireViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Gestionnaire.objects.filter(
            organisation__proprietaire=self.request.user
        )

    def get_serializer_class(self):
        if self.action == "create":
            return GestionnaireCreateSerializer
        return GestionnaireSerializer

    def perform_create(self, serializer):
        organisation = get_object_or_404(Organisation, proprietaire=self.request.user)
        serializer.save(organisation=organisation)

    @action(detail=True, methods=["post"])
    def activer_desactiver(self, request, pk=None):
        gestionnaire = self.get_object()
        gestionnaire.actif = not gestionnaire.actif
        gestionnaire.save()
        statut = "activé" if gestionnaire.actif else "désactivé"
        return Response({
            "message": f"Gestionnaire {statut} avec succès",
            "actif": gestionnaire.actif
        })


# =====================================================
# Organisation complète
# =====================================================

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def mon_organisation_complete(request):
    """
    Retourne l'organisation complète pour le dashboard d'un gestionnaire ou d'un propriétaire.
    """
    try:
        organisation = None

        # Si l'utilisateur est un gestionnaire et a un profil Gestionnaire
        if hasattr(request.user, "gestionnaire_profile") and request.user.gestionnaire_profile:
            gestionnaire = request.user.gestionnaire_profile
            organisation = gestionnaire.organisation  # <-- récupération via le gestionnaire
        else:
            # Sinon, si c'est le propriétaire
            organisation = Organisation.objects.get(proprietaire=request.user)

        if not organisation:
            return Response({"error": "Aucune organisation trouvée"}, status=404)

        serializer = OrganisationCompleteSerializer(organisation)
        return Response(serializer.data)

    except Organisation.DoesNotExist:
        return Response({"error": "Aucune organisation trouvée"}, status=404)
# =====================================================
# Modifier organisation
# =====================================================
@api_view(["PUT"])
@permission_classes([permissions.IsAuthenticated])
def modifier_organisation_base(request):
    organisation = get_object_or_404(Organisation, proprietaire=request.user)
    champs_modifiables = ["nom", "secteur", "emailContact", "telephone", "adresse", "ville", "pays", "siteWeb"]

    for champ in champs_modifiables:
        if champ in request.data:
            setattr(organisation, champ, request.data[champ])

    organisation.save()
    return Response({
        "message": "Informations mises à jour",
        "organisation": {
            "id": organisation.id,
            "nom": organisation.nom,
            "secteur": organisation.secteur,
            "emailContact": organisation.emailContact,
            "telephone": organisation.telephone,
            "adresse": organisation.adresse,
            "ville": organisation.ville,
            "pays": organisation.pays,
            "siteWeb": organisation.siteWeb
        }
    })


# =====================================================
# Demande changement abonnement
# =====================================================
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def changer_abonnement(request):
    organisation = get_object_or_404(Organisation, proprietaire=request.user)
    serializer = ChangerAbonnementSerializer(data=request.data)

    if serializer.is_valid():
        # Vérifier si une demande en attente existe déjà
        if DemandeAbonnement.objects.filter(organisation=organisation, statut="en_attente").exists():
            return Response({"error": "Une demande est déjà en cours"}, status=status.HTTP_400_BAD_REQUEST)

        demande = DemandeAbonnement.objects.create(
            organisation=organisation,
            type_demande=serializer.validated_data["type"],
            montant_propose=serializer.validated_data["montant_propose"],
            raison=serializer.validated_data.get("raison", "")
        )

        return Response({
            "message": "Demande envoyée avec succès",
            "demande": DemandeAbonnementSerializer(demande).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================================
# Historique demandes abonnement
# =====================================================
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def mes_demandes_abonnement(request):
    organisation = get_object_or_404(Organisation, proprietaire=request.user)
    demandes = DemandeAbonnement.objects.filter(organisation=organisation).order_by("-date_demande")
    serializer = DemandeAbonnementSerializer(demandes, many=True)
    return Response(serializer.data)
