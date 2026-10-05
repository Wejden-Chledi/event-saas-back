# apps/payments/serializers.py

# Import du framework Django REST pour créer des serializers
from rest_framework import serializers

# Import du modèle Paiement
from .models import Paiement

# Librairie Stripe pour gérer les paiements en ligne
import stripe

# Accès aux variables de configuration Django
from django.conf import settings

# Classes nécessaires pour créer une API personnalisée
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Import du modèle Inscription lié au paiement
from apps.inscriptions.models import Inscription


# Configuration de la clé secrète Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreatePaymentIntentView(APIView):
    """
    API permettant de créer une intention de paiement Stripe.
    Elle retourne au frontend le clientSecret nécessaire
    pour finaliser le paiement.
    """

    def post(self, request, inscription_id):

        try:
            # Récupération de l'inscription du participant connecté
            inscription = Inscription.objects.get(
                id=inscription_id,
                participant=request.user
            )

            # Vérification que l'inscription n'a pas déjà été payée
            if inscription.statut == 'paye':
                return Response(
                    {'error': 'Cette inscription est déjà payée.'},
                    status=status.HTTP_400_BAD_REQUEST
                )


            # Création d'une intention de paiement Stripe
            # Le montant Stripe doit être envoyé en centimes
            intent = stripe.PaymentIntent.create(
                amount=int(inscription.evenement.prix * 100),
                currency='eur',

                # Informations supplémentaires envoyées à Stripe
                metadata={
                    'inscription_id': str(inscription.id),
                    'user_email': request.user.email
                },

                # Activation automatique des moyens de paiement
                automatic_payment_methods={'enabled': True},
            )


            # Association de l'identifiant Stripe
            # avec l'objet Paiement enregistré en base
            if inscription.paiement:
                inscription.paiement.external_id = intent.id
                inscription.paiement.save()


            # Retour des informations nécessaires au frontend
            return Response({
                'clientSecret': intent.client_secret,
                'paymentIntentId': intent.id
            })


        # Cas où l'inscription n'existe pas
        except Inscription.DoesNotExist:
            return Response(
                {'error': 'Inscription non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


        # Gestion des erreurs générales
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



class PaiementSerializer(serializers.ModelSerializer):
    """
    Serializer permettant de transformer les données
    du paiement en format JSON pour l'API.
    """

    # Récupération du titre de l'événement associé
    evenement_titre = serializers.CharField(
        source="inscription.evenement.titre",
        read_only=True
    )

    # Récupération de l'identifiant de l'événement
    evenement_id = serializers.UUIDField(
        source="inscription.evenement.id",
        read_only=True
    )

    # Affichage du libellé du statut
    # Exemple : confirme -> Confirmé
    statut_label = serializers.CharField(
        source="get_statut_display",
        read_only=True
    )


    class Meta:

        # Modèle utilisé par ce serializer
        model = Paiement

        # Champs exposés dans l'API
        fields = [
            "id",
            "montant",
            "devise",
            "date_paiement",
            "statut",
            "statut_label",
            "mode",
            "reference_transaction",
            "external_id",
            "description",
            "evenement_titre",
            "evenement_id"
        ]

        # Champs protégés non modifiables depuis l'API
        read_only_fields = [
            "id",
            "statut",
            "date_paiement",
            "reference_transaction",
            "external_id"
        ]