# apps/users/views/profile_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.serializers import UserSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    return Response(UserSerializer(user).data)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_view(request):
    user = request.user
    data = request.data
    for field in ["nom", "prenom", "email", "telephone", "date_naissance", "adresse", "ville", "pays"]:
        if field in data:
            setattr(user, field, data[field])
    password = data.get("password")
    if password:
        user.set_password(password)
    user.save()
    return Response({"message": "Profil mis à jour", "user": UserSerializer(user).data})