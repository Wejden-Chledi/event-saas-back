# apps/payments/views.py

# Librairie Stripe pour gérer les paiements
import stripe

# Accès aux paramètres Django (clé Stripe)
from django.conf import settings

# Fonction permettant de récupérer un objet ou retourner 404
from django.shortcuts import get_object_or_404

# Classes génériques et permissions REST Framework
from rest_framework import generics, permissions, status

# Classe de vue API personnalisée
from rest_framework.views import APIView

# Réponse HTTP REST
from rest_framework.response import Response


# Modèle et serializer liés aux paiements
from .models import Paiement
from .serializers import PaiementSerializer

# Modèle inscription associé au paiement
from apps.inscriptions.models import Inscription



# Initialisation de Stripe avec la clé secrète du projet
stripe.api_key = settings.STRIPE_SECRET_KEY



# =====================================================
# CRÉATION DE L'INTENTION DE PAIEMENT (STRIPE)
# =====================================================

class CreatePaymentIntentView(APIView):
    """
    Génère une intention de paiement Stripe.
    Le clientSecret retourné sera utilisé par le frontend
    pour finaliser le paiement.
    """

    # Seuls les utilisateurs connectés peuvent payer
    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, inscription_id):

        try:
            # Récupération de l'inscription du participant connecté
            # Vérification de sécurité : l'inscription appartient bien à l'utilisateur
            inscription = get_object_or_404(
                Inscription,
                id=inscription_id,
                participant=request.user
            )


            # Empêcher un double paiement
            if inscription.statut == 'paye':
                return Response(
                    {"detail": "Cette inscription est déjà réglée."},
                    status=status.HTTP_400_BAD_REQUEST
                )


            # Création d'une intention de paiement Stripe
            intent = stripe.PaymentIntent.create(

                # Stripe utilise les montants en centimes
                amount=int(inscription.evenement.prix * 100),

                currency='eur',

                # Informations associées visibles dans Stripe
                metadata={
                    'inscription_id': str(inscription.id),
                    'user_email': request.user.email
                },

                # Activation automatique des moyens de paiement
                automatic_payment_methods={'enabled': True},
            )


            # Sauvegarde de l'identifiant Stripe
            # afin de suivre le paiement dans notre base
            if inscription.paiement:
                inscription.paiement.external_id = intent.id
                inscription.paiement.save()


            # Retour des informations nécessaires au frontend
            return Response({
                'clientSecret': intent.client_secret,
                'paymentIntentId': intent.id
            }, status=status.HTTP_200_OK)


        # Gestion des erreurs Stripe ou système
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



# =====================================================
# LISTER ET DÉTAILLER LES PAIEMENTS
# =====================================================


class PaiementListView(generics.ListAPIView):

    # Serializer utilisé pour transformer les paiements en JSON
    serializer_class = PaiementSerializer

    # Accès réservé aux utilisateurs connectés
    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):

        # Retourne uniquement les paiements
        # appartenant au participant connecté
        return Paiement.objects.filter(
            inscription__participant=self.request.user
        ).select_related(
            'inscription__evenement'
        ).order_by('-date_paiement')



class PaiementDetailView(generics.RetrieveAPIView):

    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Recherche d'un paiement par son UUID
    lookup_field = "id"


    def get_queryset(self):

        # Sécurité : l'utilisateur ne peut voir
        # que ses propres paiements
        return Paiement.objects.filter(
            inscription__participant=self.request.user
        )



# =====================================================
# CONFIRMATION ET ACTIONS SUR LES PAIEMENTS
# =====================================================


class PaiementConfirmView(APIView):
    """
    Confirme un paiement après validation Stripe.
    La confirmation déclenche automatiquement
    la génération du billet via le signal associé.
    """


    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, pk):

        # Récupération du paiement appartenant au participant
        paiement = get_object_or_404(
            Paiement,
            id=pk,
            inscription__participant=request.user
        )


        # Récupération de l'identifiant Stripe envoyé par le frontend
        stripe_intent_id = request.data.get('external_id')


        try:

            # Vérification du statut réel auprès de Stripe
            intent = stripe.PaymentIntent.retrieve(
                stripe_intent_id
            )


            # Si Stripe confirme le paiement
            if intent.status == 'succeeded':

                # Change le statut du paiement en confirmé
                # et déclenche la création du billet
                paiement.confirmer(
                    external_id=stripe_intent_id
                )


                return Response({
                    "status": "success",
                    "message": "Paiement validé et billet généré.",
                    "statut": paiement.statut
                }, status=status.HTTP_200_OK)


            else:
                return Response(
                    {
                        "detail":
                        "Le paiement n'a pas encore été validé par Stripe."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


        except Exception as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



class PaiementStatusUpdateView(APIView):

    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, pk, action):

        # Récupération du paiement du participant connecté
        paiement = get_object_or_404(
            Paiement,
            id=pk,
            inscription__participant=request.user
        )


        # Association entre action demandée
        # et méthode du modèle Paiement
        actions = {

            'annuler': paiement.annuler,

            'echouer': paiement.echouer,
        }


        # Exécution des actions simples
        if action in actions:

            actions[action]()

            message = f"Le paiement a été marqué comme {action}."


        # Gestion du remboursement
        elif action == 'rembourser':

            paiement.statut = 'rembourse'
            paiement.save()

            message = "Le paiement a été marqué comme remboursé."


        # Action inconnue
        else:

            return Response(
                {"detail": "Action non reconnue."},
                status=status.HTTP_400_BAD_REQUEST
            )


        # Retour du nouvel état du paiement
        return Response({

            "detail": message,

            "statut": paiement.statut,

            "inscription_statut": paiement.inscription.statut

        }, status=status.HTTP_200_OK)

    # =====================================================
# CARTE DE TEST STRIPE (pour les tests en mode test)
#4242 4242 4242 4242  Succès
#4000 0560 0400 0002  Échec
#https://dashboard.stripe.com/acct_1TEg3XPUS1NhN77R/test/payments
# =====================================================