# apps/users/views/auth_views.py

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.serializers import UserSerializer


# -------------------------------------------------
# LOGIN JWT
# -------------------------------------------------
class CustomTokenObtainPairView(TokenObtainPairView):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        # ❌ utilisateur inactif
        if user.statut != "actif":
            return Response(
                {"error": "Compte inactif"},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ génération tokens
        refresh = RefreshToken.for_user(user)

        user_data = UserSerializer(user).data

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_data,
        })


# -------------------------------------------------
# LOGOUT JWT (SAFE VERSION)
# -------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):

    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"error": "Refresh token requis"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        token = RefreshToken(refresh_token)

        # -------------------------------------------------
        # BLACKLIST SAFE MODE
        # -------------------------------------------------
        # fonctionne seulement si token blacklist activé
        if hasattr(token, "blacklist"):
            token.blacklist()

        return Response(
            {"message": "Déconnecté avec succès"},
            status=status.HTTP_200_OK
        )

    except Exception:
        return Response(
            {"error": "Token invalide"},
            status=status.HTTP_400_BAD_REQUEST
        )