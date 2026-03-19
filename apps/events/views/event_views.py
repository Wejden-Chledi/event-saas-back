from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.users.permissions import IsGestionnaire
from apps.events.serializers import (
    EvenementSerializer,
    EvenementCreateSerializer,
    EvenementUpdateSerializer,
    AssignationEvenementSerializer
)
from apps.events.models import Evenement, AssignationEvenement
from apps.users.models import Utilisateur
from ..ai_service import generate_event_description as gen_desc

# ==================================
# CREATE EVENEMENT
# ==================================
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def create_evenement_view(request):
    serializer = EvenementCreateSerializer(data=request.data)
    if serializer.is_valid():
        evenement = serializer.save(
            createur=request.user,
            organisation=request.user.organisation
        )
        return Response({
            "message": "Événement créé avec succès",
            "evenement": EvenementSerializer(evenement).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================================
# LIST & RETRIEVE EVENEMENTS
# ==================================
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def list_evenements_view(request):
    organisation = request.user.organisation
    evenements = Evenement.objects.filter(organisation=organisation)
    serializer = EvenementSerializer(evenements, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def retrieve_evenement_view(request, evenement_id):
    try:
        evenement = Evenement.objects.get(id=evenement_id, organisation=request.user.organisation)
    except Evenement.DoesNotExist:
        return Response({"error": "Événement non trouvé"}, status=404)
    serializer = EvenementSerializer(evenement)
    return Response(serializer.data)


# ==================================
# UPDATE EVENEMENT (avec validation capacité)
# ==================================
@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def update_evenement_view(request, evenement_id):
    try:
        evenement = Evenement.objects.get(id=evenement_id, organisation=request.user.organisation)
    except Evenement.DoesNotExist:
        return Response({"error": "Événement non trouvé"}, status=404)
    serializer = EvenementUpdateSerializer(evenement, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Événement mis à jour",
            "evenement": EvenementSerializer(evenement).data
        })
    return Response(serializer.errors, status=400)


# ==================================
# DELETE EVENEMENT
# ==================================
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def delete_evenement_view(request, evenement_id):
    try:
        evenement = Evenement.objects.get(id=evenement_id, organisation=request.user.organisation)
        evenement.delete()
        return Response({"message": "Événement supprimé"})
    except Evenement.DoesNotExist:
        return Response({"error": "Événement non trouvé"}, status=404)


# ==================================
# ASSIGNATION STAFF
# ==================================
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def assign_staff_view(request):
    staff_id = request.data.get("staff_id")
    evenement_id = request.data.get("evenement_id")
    if not staff_id or not evenement_id:
        return Response({"error": "staff_id et evenement_id requis"}, status=400)
    try:
        staff = Utilisateur.objects.get(id=staff_id, role="staff", organisation=request.user.organisation)
        evenement = Evenement.objects.get(id=evenement_id, organisation=request.user.organisation)
    except Utilisateur.DoesNotExist:
        return Response({"error": "Staff introuvable"}, status=404)
    except Evenement.DoesNotExist:
        return Response({"error": "Événement introuvable"}, status=404)

    assignation, created = AssignationEvenement.objects.get_or_create(
        staff=staff,
        evenement=evenement
    )
    if not created:
        return Response({"message": "Staff déjà assigné à cet événement"}, status=400)
    serializer = AssignationEvenementSerializer(assignation)
    return Response({
        "message": "Staff assigné avec succès",
        "assignation": serializer.data
    }, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def list_staff_assignes_view(request, evenement_id):
    try:
        evenement = Evenement.objects.get(id=evenement_id, organisation=request.user.organisation)
    except Evenement.DoesNotExist:
        return Response({"error": "Événement introuvable"}, status=404)
    assignations = AssignationEvenement.objects.filter(evenement=evenement)
    serializer = AssignationEvenementSerializer(assignations, many=True)
    return Response(serializer.data)