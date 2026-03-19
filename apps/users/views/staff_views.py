# apps/users/views/staff_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.serializers import StaffCreateSerializer, UserSerializer
from apps.users.permissions import IsGestionnaire
from apps.users.models import Utilisateur


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def create_staff_view(request):
    org = request.user.organisation
    if not org:
        return Response({"error": "Aucune organisation associée"}, status=400)
    serializer = StaffCreateSerializer(data=request.data, context={"organisation": org})
    if serializer.is_valid():
        staff = serializer.save()
        return Response({
            "message": "Staff créé avec succès",
            "user": UserSerializer(staff).data
        }, status=201)
    return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def list_staff_view(request):
    org = request.user.organisation
    staff_list = org.utilisateurs.filter(role="staff")
    return Response(UserSerializer(staff_list, many=True).data)

@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def update_staff_view(request, staff_id):
    
    org = request.user.organisation
    try:
        staff = Utilisateur.objects.get(id=staff_id, role="staff", organisation=org)
    except Utilisateur.DoesNotExist:
        return Response({"error": "Staff non trouvé"}, status=404)
    data = request.data
    for field in ["nom", "prenom", "email", "telephone", "date_naissance", "adresse", "ville", "pays", "statut"]:
        if field in data:
            setattr(staff, field, data[field])
    staff.save()
    return Response({"message": "Staff mis à jour", "user": UserSerializer(staff).data})

@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsGestionnaire])
def delete_staff_view(request, staff_id):
    
    org = request.user.organisation
    try:
        staff = Utilisateur.objects.get(id=staff_id, role="staff", organisation=org)
        staff.delete()
        return Response({"message": "Staff supprimé"})
    except Utilisateur.DoesNotExist:
        return Response({"error": "Staff non trouvé"}, status=404)