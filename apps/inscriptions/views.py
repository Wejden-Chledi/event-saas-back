# apps/inscriptions/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.inscriptions.models import Inscription, Billet
from apps.inscriptions.serializers import (
    InscriptionSerializer,
    InscriptionCreateSerializer,
    BilletSerializer
)
from apps.payments.models import Paiement
from apps.payments.serializers import PaiementConfirmSerializer


# ================================
# Créer une inscription
# ================================
class InscriptionCreateView(generics.CreateAPIView):
    """
    Permet au participant de s'inscrire à un événement.
    Vérifie les places disponibles et génère automatiquement un paiement.
    """
    queryset = Inscription.objects.all()
    serializer_class = InscriptionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


# ================================
# Lister les inscriptions du participant
# ================================
class ParticipantInscriptionsListView(generics.ListAPIView):
    """
    Affiche toutes les inscriptions de l'utilisateur connecté.
    """
    serializer_class = InscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Inscription.objects.filter(participant=self.request.user).order_by('-date_inscription')


# ================================
# Détails d'une inscription
# ================================
class InscriptionDetailView(generics.RetrieveAPIView):
    """
    Récupère le détail d'une inscription (participant, événement, paiement, statut).
    """
    queryset = Inscription.objects.all()
    serializer_class = InscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"


# ================================
# Lister les billets du participant
# ================================
class BilletListView(generics.ListAPIView):
    """
    Affiche tous les billets du participant connecté.
    """
    serializer_class = BilletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Billet.objects.filter(inscription__participant=self.request.user)


# ================================
# Détail d'un billet
# ================================
class BilletDetailView(generics.RetrieveAPIView):
    """
    Récupère un billet précis avec QR code et PDF.
    """
    queryset = Billet.objects.all()
    serializer_class = BilletSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"


# ================================
# Confirmer un paiement (via webhook ou manuel)
# ================================
class PaiementConfirmView(APIView):
    """
    Confirme le paiement et déclenche automatiquement la génération du billet et la notification.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            paiement = Paiement.objects.get(id=id)
            paiement.confirmer()
            return Response({"detail": "Paiement confirmé"}, status=status.HTTP_200_OK)
        except Paiement.DoesNotExist:
            return Response({"detail": "Paiement non trouvé"}, status=status.HTTP_404_NOT_FOUND)


# ================================
# Optionnel : annuler une inscription
# ================================
class InscriptionCancelView(APIView):
    """
    Annule une inscription et met éventuellement le paiement en annule.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            inscription = Inscription.objects.get(id=id, participant=request.user)
            inscription.statut = "annule"
            inscription.save()
            if inscription.paiement:
                inscription.paiement.annuler()
            return Response({"detail": "Inscription annulée"}, status=status.HTTP_200_OK)
        except Inscription.DoesNotExist:
            return Response({"detail": "Inscription non trouvée"}, status=status.HTTP_404_NOT_FOUND)