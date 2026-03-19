# apps/organisations/views/abonnement_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from apps.organisations.models import Organisation, Abonnement
from apps.organisations.serializers import AbonnementSerializer
from apps.users.permissions import IsProprietaire
from rest_framework.permissions import IsAuthenticated


# ==============================
# UPDATE ABONNEMENT
# ==============================
@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsProprietaire])
def update_abonnement_view(request):
    user = request.user

    try:
        organisation = Organisation.objects.get(proprietaire=user)
    except Organisation.DoesNotExist:
        return Response({"error": "Organisation non trouvée"}, status=404)

    abonnement = organisation.abonnement

    if not abonnement:
        return Response({"error": "Aucun abonnement"}, status=400)

    data = request.data

    for field in ["plan", "date_fin", "statut"]:
        if field in data:
            setattr(abonnement, field, data[field])

    abonnement.save()

    return Response({
        "message": "Abonnement mis à jour",
        "abonnement": AbonnementSerializer(abonnement).data
    })


# ==============================
# GET ABONNEMENT
# ==============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_abonnement_view(request):
    user = request.user

    organisation = user.organisation if user.role != "proprietaire" else \
        Organisation.objects.filter(proprietaire=user).first()

    if not organisation or not organisation.abonnement:
        return Response({"error": "Aucun abonnement"}, status=404)

    return Response(AbonnementSerializer(organisation.abonnement).data)