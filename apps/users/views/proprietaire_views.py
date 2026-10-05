# apps/users/views/proprietaire_views.py
#
# Ce fichier contient la vue permettant l'inscription
# d'un propriétaire (Propriétaire d'organisation).
#
# Cette API est publique et ne nécessite pas
# d'authentification.
# ============================================================================

from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from rest_framework import status
from rest_framework.response import Response
from apps.users.serializers import (
    ProprietaireRegisterSerializer,
    UserSerializer,
)


# ============================================================================
# INSCRIPTION D'UN PROPRIÉTAIRE
# ============================================================================

@api_view(["POST"])

# L'inscription est accessible à tous les utilisateurs,
# même sans connexion.
@permission_classes([AllowAny])
def register_proprietaire_view(request):
    """
    API permettant de créer un compte propriétaire.

    Route :
        POST /api/register/proprietaire/

    Cette vue :
        - reçoit les données du propriétaire ;
        - valide les informations ;
        - crée le compte ;
        - retourne les informations du propriétaire créé.
    """

    # Création du serializer avec les données
    # reçues dans la requête HTTP.
    serializer = ProprietaireRegisterSerializer(data=request.data)

    # Vérifie que toutes les données sont valides.
    if serializer.is_valid():

        # Création du compte propriétaire.
        user = serializer.save()

        # Retourne un message de succès
        # ainsi que les informations du propriétaire créé.
        return Response(
            {
                "message": "Compte propriétaire créé avec succès",

                "user": UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )

    # Si les données sont invalides,
    # retourne les erreurs de validation.
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )