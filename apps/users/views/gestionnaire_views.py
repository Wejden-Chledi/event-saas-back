# apps/users/views/gestionnaire_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.serializers import GestionnaireCreateSerializer, UserSerializer
from apps.users.permissions import IsProprietaire
from apps.users.models import Utilisateur


# ==============================
# CREATE GESTIONNAIRE
# ==============================
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsProprietaire])
def create_gestionnaire_view(request):

    org = request.user.organisation

    if not org:
        return Response({"error": "Aucune organisation associée"}, status=400)

    serializer = GestionnaireCreateSerializer(
        data=request.data,
        context={"organisation": org}
    )

    if serializer.is_valid():
        gestionnaire = serializer.save()
        return Response({
            "message": "Gestionnaire créé avec succès",
            "user": UserSerializer(gestionnaire).data
        }, status=201)

    return Response(serializer.errors, status=400)


# ==============================
# LIST GESTIONNAIRES
# ==============================
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsProprietaire])
def list_gestionnaires_view(request):

    org = request.user.organisation

    if not org:
        return Response({"error": "Aucune organisation associée"}, status=400)

    users = org.utilisateurs.filter(role="gestionnaire")

    return Response(UserSerializer(users, many=True).data)


# ==============================
# UPDATE GESTIONNAIRE
# ==============================
@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsProprietaire])
def update_gestionnaire_view(request, gestionnaire_id):

    org = request.user.organisation

    try:
        gestionnaire = Utilisateur.objects.get(
            id=gestionnaire_id,
            role="gestionnaire",
            organisation=org   # ✅ SÉCURITÉ MULTI-TENANT
        )
    except Utilisateur.DoesNotExist:
        return Response({"error": "Gestionnaire non trouvé"}, status=404)

    data = request.data

    for field in ["nom", "prenom", "email", "telephone", "date_naissance", "adresse", "ville", "pays", "statut"]:
        if field in data:
            setattr(gestionnaire, field, data[field])

    gestionnaire.save()

    return Response({
        "message": "Gestionnaire mis à jour",
        "user": UserSerializer(gestionnaire).data
    })


# ==============================
# DELETE GESTIONNAIRE
# ==============================
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsProprietaire])
def delete_gestionnaire_view(request, gestionnaire_id):

    org = request.user.organisation

    try:
        gestionnaire = Utilisateur.objects.get(
            id=gestionnaire_id,
            role="gestionnaire",
            organisation=org   # ✅ SÉCURITÉ
        )
        gestionnaire.delete()

        return Response({"message": "Gestionnaire supprimé"})

    except Utilisateur.DoesNotExist:
        return Response({"error": "Gestionnaire non trouvé"}, status=404)