# apps/payments/serializers.py
from rest_framework import serializers
from .models import Paiement
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.inscriptions.models import Inscription

# Utilisation de la clé secrète Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentIntentView(APIView):
    """
    Vue pour créer une intention de paiement Stripe.
    Elle renvoie un client_secret au frontend.
    """
    def post(self, request, inscription_id):
        try:
            # 1. Récupérer l'inscription appartenant à l'utilisateur
            inscription = Inscription.objects.get(id=inscription_id, participant=request.user)
            
            # 2. Sécurité : Vérifier si l'inscription n'est pas déjà payée
            if inscription.statut == 'paye':
                return Response({'error': 'Cette inscription est déjà payée.'}, status=status.HTTP_400_BAD_REQUEST)

            # 3. Créer le PaymentIntent chez Stripe (montant en centimes)
            intent = stripe.PaymentIntent.create(
                amount=int(inscription.evenement.prix * 100),
                currency='eur',
                metadata={
                    'inscription_id': str(inscription.id),
                    'user_email': request.user.email
                },
                automatic_payment_methods={'enabled': True},
            )

            # 4. Sauvegarder l'ID de l'intention Stripe dans l'objet Paiement lié
            if inscription.paiement:
                inscription.paiement.external_id = intent.id
                inscription.paiement.save()

            return Response({
                'clientSecret': intent.client_secret,
                'paymentIntentId': intent.id
            })
            
        except Inscription.DoesNotExist:
            return Response({'error': 'Inscription non trouvée'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaiementSerializer(serializers.ModelSerializer):
    evenement_titre = serializers.CharField(source="inscription.evenement.titre", read_only=True)
    evenement_id = serializers.UUIDField(source="inscription.evenement.id", read_only=True)
    statut_label = serializers.CharField(source="get_statut_display", read_only=True)

    class Meta:
        model = Paiement
        fields = [
            "id", "montant", "devise", "date_paiement", "statut", "statut_label",
            "mode", "reference_transaction", "external_id", 
            "description", "evenement_titre", "evenement_id"
        ]
        read_only_fields = ["id", "statut", "date_paiement", "reference_transaction", "external_id"]