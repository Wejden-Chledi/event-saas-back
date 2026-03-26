# apps/payments/views.py
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Paiement
from .serializers import PaiementSerializer
from apps.inscriptions.models import Inscription

# Initialisation de Stripe avec la clé secrète
stripe.api_key = settings.STRIPE_SECRET_KEY
# =====================================================
# CARTE DE TEST STRIPE (pour les tests en mode test)
#4242 4242 4242 4242  Succès
#4000 0560 0400 0002  Échec
#https://dashboard.stripe.com/acct_1TEg3XPUS1NhN77R/test/payments
# =====================================================
# CRÉATION DE L'INTENTION DE PAIEMENT (STRIPE)
# =====================================================
class CreatePaymentIntentView(APIView):
    """
    Génère un clientSecret Stripe pour permettre au frontend 
    de finaliser le paiement.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, inscription_id):
        try:
            # Récupérer l'inscription (sécurité : appartient à l'user)
            inscription = get_object_or_404(Inscription, id=inscription_id, participant=request.user)
            
            if inscription.statut == 'paye':
                return Response({"detail": "Cette inscription est déjà réglée."}, status=status.HTTP_400_BAD_REQUEST)

            # Créer le PaymentIntent sur Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(inscription.evenement.prix * 100), # Stripe utilise les centimes
                currency='eur',
                metadata={
                    'inscription_id': str(inscription.id),
                    'user_email': request.user.email
                },
                automatic_payment_methods={'enabled': True},
            )

            # On stocke l'ID Stripe dans notre objet Paiement pour le suivi
            if inscription.paiement:
                inscription.paiement.external_id = intent.id
                inscription.paiement.save()

            return Response({
                'clientSecret': intent.client_secret,
                'paymentIntentId': intent.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =====================================================
# LISTER ET DÉTAILLER LES PAIEMENTS
# =====================================================
class PaiementListView(generics.ListAPIView):
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Paiement.objects.filter(
            inscription__participant=self.request.user
        ).select_related('inscription__evenement').order_by('-date_paiement')


class PaiementDetailView(generics.RetrieveAPIView):
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Paiement.objects.filter(inscription__participant=self.request.user)


# =====================================================
# CONFIRMATION ET ACTIONS
# =====================================================
class PaiementConfirmView(APIView):
    """
    Appelée par le frontend une fois que Stripe a confirmé le paiement.
    Vérifie l'état de l'intention auprès de Stripe pour plus de sécurité.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk): 
        paiement = get_object_or_404(Paiement, id=pk, inscription__participant=request.user)
        stripe_intent_id = request.data.get('external_id')

        try:
            # Vérification de sécurité optionnelle mais recommandée auprès de Stripe
            intent = stripe.PaymentIntent.retrieve(stripe_intent_id)
            
            if intent.status == 'succeeded':
                # La méthode confirmer() du modèle déclenche le signal de création de billet
                paiement.confirmer(external_id=stripe_intent_id)
                return Response({
                    "status": "success",
                    "message": "Paiement validé et billet généré.",
                    "statut": paiement.statut
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Le paiement n'a pas encore été validé par Stripe."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaiementStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action): 
        paiement = get_object_or_404(Paiement, id=pk, inscription__participant=request.user)

        actions = {
            'annuler': paiement.annuler,
            'echouer': paiement.echouer,
        }

        if action in actions:
            actions[action]()
            message = f"Le paiement a été marqué comme {action}."
        elif action == 'rembourser':
            paiement.statut = 'rembourse'
            paiement.save()
            message = "Le paiement a été marqué comme remboursé."
        else:
            return Response({"detail": "Action non reconnue."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": message, 
            "statut": paiement.statut,
            "inscription_statut": paiement.inscription.statut
        }, status=status.HTTP_200_OK)