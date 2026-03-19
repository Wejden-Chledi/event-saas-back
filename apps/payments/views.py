# apps/payments/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Paiement
from .serializers import PaiementSerializer, PaiementConfirmSerializer


# ================================
# Lister les paiements de l'utilisateur
# ================================
class PaiementListView(generics.ListAPIView):
    """
    Liste tous les paiements de l'utilisateur connecté.
    """
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Paiement.objects.filter(inscription__participant=self.request.user).order_by('-date_paiement')


# ================================
# Détail d'un paiement
# ================================
class PaiementDetailView(generics.RetrieveAPIView):
    """
    Détail d'un paiement spécifique.
    """
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"


# ================================
# Confirmer un paiement
# ================================
class PaiementConfirmView(APIView):
    """
    Confirme un paiement et déclenche éventuellement la génération du billet et notification.
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
# Annuler un paiement
# ================================
class PaiementCancelView(APIView):
    """
    Annule un paiement existant.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            paiement = Paiement.objects.get(id=id)
            paiement.annuler()
            return Response({"detail": "Paiement annulé"}, status=status.HTTP_200_OK)
        except Paiement.DoesNotExist:
            return Response({"detail": "Paiement non trouvé"}, status=status.HTTP_404_NOT_FOUND)


# ================================
# Marquer un paiement comme échoué
# ================================
class PaiementFailView(APIView):
    """
    Marque un paiement comme échoué.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            paiement = Paiement.objects.get(id=id)
            paiement.echouer()
            return Response({"detail": "Paiement échoué"}, status=status.HTTP_200_OK)
        except Paiement.DoesNotExist:
            return Response({"detail": "Paiement non trouvé"}, status=status.HTTP_404_NOT_FOUND)