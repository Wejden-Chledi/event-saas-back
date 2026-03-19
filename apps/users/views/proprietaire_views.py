# apps/users/views/proprietaire_views.py
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from apps.users.serializers import ProprietaireRegisterSerializer, UserSerializer

@api_view(["POST"])
def register_proprietaire_view(request):
    serializer = ProprietaireRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "Compte propriétaire créé avec succès",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)