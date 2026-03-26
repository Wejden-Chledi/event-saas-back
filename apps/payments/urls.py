# apps/payments/urls.py
from django.urls import path
from .views import (
    PaiementListView,
    PaiementDetailView,
    PaiementConfirmView,
    PaiementStatusUpdateView,
    CreatePaymentIntentView
)

urlpatterns = [
    path('', PaiementListView.as_view(), name='paiement-list'),
    
    # Route pour générer le clientSecret Stripe
    path('create-intent/<uuid:inscription_id>/', CreatePaymentIntentView.as_view(), name='paiement-create-intent'),
    
    path('<uuid:id>/', PaiementDetailView.as_view(), name='paiement-detail'),
    path('<uuid:pk>/confirmer/', PaiementConfirmView.as_view(), name='paiement-confirmer'),
    
    # Actions dynamiques (annuler, echouer, rembourser)
    path('<uuid:pk>/<str:action>/', PaiementStatusUpdateView.as_view(), name='paiement-action'),
]