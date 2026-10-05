# apps/users/views/auth_views.py
# Gestion des jetons JWT pour la connexion et la déconnexion


from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.serializers import UserSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Surcharge la vue de connexion par défaut pour ajouter une vérification de statut.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        # Sécurité : On bloque la connexion si l'utilisateur est marqué 'inactif'
        if user.statut != "actif":
            return Response({"error": "Compte inactif"}, status=status.HTTP_403_FORBIDDEN)

        # Génération des tokens JWT (Access = accès temporaire, Refresh = renouvellement)
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_data,
        })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Déconnexion : blacklist le jeton pour qu'il ne puisse plus être utilisé.
    """
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({"error": "Refresh token requis"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        # Si le système de blacklist est configuré, on invalide le jeton
        if hasattr(token, "blacklist"):
            token.blacklist()
        return Response({"message": "Déconnecté avec succès"}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"error": "Token invalide"}, status=status.HTTP_400_BAD_REQUEST)