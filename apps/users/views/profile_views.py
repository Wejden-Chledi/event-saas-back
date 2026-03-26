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
    serializer = UserSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        updated_user = serializer.save()
        
        password = request.data.get("password")
        if password:
            updated_user.set_password(password)
            updated_user.save()
            
        return Response({
            "message": "Profil mis à jour", 
            "user": UserSerializer(updated_user).data # ✅ Retourne l'utilisateur ici
        })
    return Response(serializer.errors, status=400)