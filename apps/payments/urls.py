# apps/payments/urls.py


# Import des fonctions de gestion des URLs Django
from django.urls import path


# Import des vues liées aux paiements
from .views import (
    PaiementListView,
    PaiementDetailView,
    PaiementConfirmView,
    PaiementStatusUpdateView,
    CreatePaymentIntentView
)



# Définition des routes de l'application paiement
urlpatterns = [


    # Liste des paiements du participant connecté
    path(
        '',
        PaiementListView.as_view(),
        name='paiement-list'
    ),



    # Création d'une intention de paiement Stripe
    # Retourne le clientSecret utilisé par le frontend
    path(
        'create-intent/<uuid:inscription_id>/',
        CreatePaymentIntentView.as_view(),
        name='paiement-create-intent'
    ),



    # Consultation d'un paiement spécifique
    # Recherche par identifiant UUID du paiement
    path(
        '<uuid:id>/',
        PaiementDetailView.as_view(),
        name='paiement-detail'
    ),



    # Confirmation du paiement après validation Stripe
    # Cette action met à jour le statut du paiement
    # et déclenche la génération du billet
    path(
        '<uuid:pk>/confirmer/',
        PaiementConfirmView.as_view(),
        name='paiement-confirmer'
    ),



    # Actions dynamiques sur un paiement :
    # - annuler
    # - echouer
    # - rembourser
    path(
        '<uuid:pk>/<str:action>/',
        PaiementStatusUpdateView.as_view(),
        name='paiement-action'
    ),
]