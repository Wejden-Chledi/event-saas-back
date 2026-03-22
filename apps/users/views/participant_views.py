# apps/users/views/participant_views.py
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from apps.users.serializers import ParticipantRegisterSerializer, UserSerializer
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

@api_view(["POST"])
@permission_classes([AllowAny])
def register_participant_view(request):
    serializer = ParticipantRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "Compte participant créé avec succès",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)