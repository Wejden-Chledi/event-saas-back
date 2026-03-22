from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.organisations.models import Organisation
from apps.organisations.serializers import AbonnementSerializer
from apps.users.permissions import IsProprietaire
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta

# Durée et prix par plan
duree_map = {
    "gratuit": 30,
    "basique": 30,
    "pro": 90,
    "premium": 365
}

PLAN_PRICES = {
    "gratuit": 0,
    "basique": 50,
    "pro": 140,
    "premium": 500
}

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

    if "plan" in data:
        plan = data["plan"]
        abonnement.plan = plan
        abonnement.montant = PLAN_PRICES.get(plan, 0)

        # ⚡ Corrigé : date_debut si vide, et date_fin calculée avec durée du plan
        if not abonnement.date_debut:
            abonnement.date_debut = datetime.now().date()
        abonnement.date_fin = abonnement.date_debut + timedelta(days=duree_map.get(plan, 30))

    if "statut" in data:
        abonnement.statut = data["statut"]

    if "date_fin" in data:
        try:
            # Accepter seulement la date (YYYY-MM-DD)
            abonnement.date_fin = datetime.fromisoformat(data["date_fin"]).date()
        except ValueError:
            pass  # ignore format invalide

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