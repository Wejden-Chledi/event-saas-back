# apps/payments/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Paiement
from .serializers import PaiementSerializer

# =====================================================
# Lister les paiements de l'utilisateur
# =====================================================
class PaiementListView(generics.ListAPIView):
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Correction : on utilise 'inscription' au lieu de 'inscription_set'
        return Paiement.objects.filter(
            inscription__participant=self.request.user
        ).distinct().order_by('-date_paiement')


# =====================================================
# Confirmer un paiement (Action POST)
# =====================================================
class PaiementConfirmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            # Correction ici aussi : 'inscription__participant'
            paiement = Paiement.objects.get(
                id=id, 
                inscription__participant=request.user
            )
            paiement.confirmer()
            return Response(
                {"detail": "Paiement confirmé avec succès.", "statut": paiement.statut}, 
                status=status.HTTP_200_OK
            )
        except Paiement.DoesNotExist:
            return Response(
                {"detail": "Paiement non trouvé ou accès refusé."}, 
                status=status.HTTP_404_NOT_FOUND
            )

# =====================================================
# Détail d'un paiement
# =====================================================
class PaiementDetailView(generics.RetrieveAPIView):
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Paiement.objects.filter(inscription__participant=self.request.user)

# =====================================================
# Annuler un paiement
# =====================================================
class PaiementCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            paiement = Paiement.objects.get(id=id, inscription__participant=request.user)
            paiement.annuler()
            return Response({"detail": "Paiement annulé"}, status=status.HTTP_200_OK)
        except Paiement.DoesNotExist:
            return Response({"detail": "Paiement non trouvé"}, status=status.HTTP_404_NOT_FOUND)

# =====================================================
# Marquer un paiement comme échoué
# =====================================================
class PaiementFailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            paiement = Paiement.objects.get(id=id, inscription__participant=request.user)
            paiement.echouer()
            return Response({"detail": "Paiement échoué"}, status=status.HTTP_200_OK)
        except Paiement.DoesNotExist:
            return Response({"detail": "Paiement non trouvé"}, status=status.HTTP_404_NOT_FOUND)