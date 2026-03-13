from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import ProprietaireRegisterSerializer, ParticipantRegisterSerializer

Utilisateur = get_user_model()


# -----------------------------
# LOGIN avec JWT
# -----------------------------
class CustomTokenObtainPairView(TokenObtainPairView):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user

            # Générer les tokens
            refresh = RefreshToken.for_user(user)

            # Construire la réponse
            user_data = {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role,
                "telephone": getattr(user, "telephone", ""),
            }

            response_data = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_data,
                "role": user.role
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# LOGOUT JWT
# -----------------------------
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token requis"}, status=400)
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Déconnecté avec succès"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)


# -----------------------------
# PROFIL utilisateur
# -----------------------------
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    try:
        user = request.user
        data = {
            "id": user.id,
            "email": user.email,
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role,
            "telephone": getattr(user, "telephone", ""),
        }

        # Organisation si gestionnaire
        if hasattr(user, "gestionnaire_profile"):
            data["organisation_id"] = user.gestionnaire_profile.organisation.id

        return Response(data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# -----------------------------
# INSCRIPTION propriétaire
# -----------------------------
@api_view(["POST"])
def register_proprietaire_view(request):
    serializer = ProprietaireRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "Compte propriétaire créé avec succès",
            "user": {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# INSCRIPTION participant
# -----------------------------
@api_view(["POST"])
def register_participant_view(request):
    serializer = ParticipantRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "Compte participant créé avec succès",
            "user": {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role,
                "telephone": user.telephone
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# INSCRIPTION générique
# -----------------------------
@api_view(["POST"])
def register_view(request):
    data = request.data
    if "nom_organisation" in data and "secteur" in data:
        # Proprietaire
        serializer = ProprietaireRegisterSerializer(data=data)
        message = "Compte propriétaire créé avec succès"
    else:
        # Participant
        serializer = ParticipantRegisterSerializer(data=data)
        message = "Compte participant créé avec succès"

    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": message,
            "user": {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role
            }
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)