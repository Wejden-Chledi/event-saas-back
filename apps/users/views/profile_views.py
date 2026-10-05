# ============================================================================
# Fichier : apps/users/views/profile_views.py
#
# Ce fichier contient les API permettant à un utilisateur authentifié :
#
#   - de consulter son profil ;
#   - de modifier ses informations personnelles.
#
# Ces opérations sont accessibles uniquement après authentification.
# ============================================================================

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.serializers import UserSerializer


# ============================================================================
# CONSULTATION DU PROFIL
# ============================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    API permettant à l'utilisateur authentifié
    de consulter son profil.

    Route :
        GET /api/profile/

    L'utilisateur est automatiquement récupéré
    grâce au système d'authentification Django REST Framework.
    """

    # Utilisateur actuellement connecté.
    user = request.user

    # Retourne les informations de l'utilisateur
    # sous forme JSON.
    return Response(
        UserSerializer(user).data
    )


# ============================================================================
# MODIFICATION DU PROFIL
# ============================================================================

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_view(request):
    """
    API permettant à un utilisateur connecté
    de modifier son profil.

    Route :
        PUT /api/profile/update/

    Les champs peuvent être modifiés partiellement
    grâce à l'option partial=True.
    """

    # Récupère l'utilisateur connecté.
    user = request.user

    # Initialise le serializer avec :
    #   - l'utilisateur existant,
    #   - les nouvelles données,
    #   - partial=True afin que tous les champs
    #     ne soient pas obligatoires.
    serializer = UserSerializer(
        user,
        data=request.data,
        partial=True
    )

    # Vérifie que les nouvelles données sont valides.
    if serializer.is_valid():
        updated_user = serializer.save()
        password = request.data.get("password")

        if password:
            updated_user.set_password(password)
            updated_user.save()
        return Response(
            {
                "message": "Profil mis à jour",

                "user": UserSerializer(
                    updated_user
                ).data
            }
        )

    # Si les données sont invalides,
    # retourne les erreurs de validation.
    return Response(
        serializer.errors,
        status=400
    )