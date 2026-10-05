# apps/users/views/participant_views.py
#
# Ce fichier contient la vue permettant à un participant
# de créer un compte sur la plateforme.
#
# Contrairement aux autres utilisateurs (Gestionnaire, Staff),
# cette inscription est publique et ne nécessite pas
# d'être authentifié.
# ============================================================================


# ==============================
# IMPORTATION DES LIBRAIRIES DRF
# ==============================

from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from apps.users.serializers import (
    ParticipantRegisterSerializer,
    UserSerializer,
)
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes


# ============================================================================
# INSCRIPTION D'UN PARTICIPANT
# ============================================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def register_participant_view(request):
    """
    API permettant à un participant de créer un compte.

    Route :
        POST /api/register/

    Cette vue :

        1. reçoit les informations du participant,
        2. valide les données,
        3. crée le compte,
        4. retourne les informations du nouvel utilisateur.

    L'accès est public grâce à la permission AllowAny.
    """

    # Création du serializer avec les données
    # envoyées dans la requête HTTP.
    serializer = ParticipantRegisterSerializer(
        data=request.data
    )

    # Vérifie que toutes les données sont valides.
    if serializer.is_valid():

        user = serializer.save()

        # Retourne un message de succès
        # ainsi que les informations du participant créé.
        return Response(
            {
                "message": "Compte participant créé avec succès",

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