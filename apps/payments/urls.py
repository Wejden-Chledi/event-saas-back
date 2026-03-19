# apps/payments/urls.py
from django.urls import path
from .views import (
    PaiementListView,
    PaiementDetailView,
    PaiementConfirmView,
    PaiementCancelView,
    PaiementFailView
)

urlpatterns = [
    # Liste des paiements
    path('', PaiementListView.as_view(), name='paiement-list'),

    # Détails d'un paiement
    path('<uuid:id>/', PaiementDetailView.as_view(), name='paiement-detail'),

    # Confirmer un paiement
    path('<uuid:id>/confirmer/', PaiementConfirmView.as_view(), name='paiement-confirmer'),

    # Annuler un paiement
    path('<uuid:id>/annuler/', PaiementCancelView.as_view(), name='paiement-annuler'),

    # Marquer un paiement comme échoué
    path('<uuid:id>/echouer/', PaiementFailView.as_view(), name='paiement-echouer'),
]