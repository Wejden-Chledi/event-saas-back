# apps/organisations/views/organisation_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from apps.organisations.models import Organisation
from apps.organisations.serializers import (
    OrganisationSerializer,
    OrganisationCompleteSerializer,
    OrganisationCreateSerializer
)
from apps.users.permissions import IsProprietaire, IsGestionnaire
from rest_framework.permissions import IsAuthenticated


# ==============================
# CREATE ORGANISATION (Owner)
# ==============================
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsProprietaire])
def create_organisation_view(request):
    user = request.user

    # Vérifier si déjà une organisation
    if Organisation.objects.filter(proprietaire=user).exists():
        return Response({"error": "Vous avez déjà une organisation"}, status=400)

    serializer = OrganisationCreateSerializer(
        data=request.data,
        context={"proprietaire": user}
    )

    if serializer.is_valid():
        organisation = serializer.save()

        return Response({
            "message": "Organisation créée avec succès",
            "organisation": OrganisationSerializer(organisation).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==============================
# GET MY ORGANISATION
# ==============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_organisation_view(request):

    organisation = request.user.organisation

    if not organisation:
        return Response({"error": "Aucune organisation trouvée"}, status=404)

    return Response(OrganisationCompleteSerializer(organisation).data)

# ==============================
# UPDATE ORGANISATION
# ==============================
@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsProprietaire])
def update_organisation_view(request):
    user = request.user

    try:
        organisation = Organisation.objects.get(proprietaire=user)
    except Organisation.DoesNotExist:
        return Response({"error": "Organisation non trouvée"}, status=404)

    data = request.data

    for field in [
        "nom", "secteur", "description", "email_contact",
        "telephone", "adresse", "ville", "pays", "site_web"
    ]:
        if field in data:
            setattr(organisation, field, data[field])

    organisation.save()

    return Response({
        "message": "Organisation mise à jour",
        "organisation": OrganisationSerializer(organisation).data
    })


# ==============================
# DELETE ORGANISATION
# ==============================
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsProprietaire])
def delete_organisation_view(request):
    user = request.user

    try:
        organisation = Organisation.objects.get(proprietaire=user)
        organisation.delete()
        return Response({"message": "Organisation supprimée"})
    except Organisation.DoesNotExist:
        return Response({"error": "Organisation non trouvée"}, status=404)