# apps/inscriptions/urls.py
from django.urls import path
from .views import (
    InscriptionCreateView,
    ParticipantInscriptionsListView,
    InscriptionDetailView,
    BilletListView,
    BilletDetailView,
    PaiementConfirmView,
    InscriptionCancelView,
)

urlpatterns = [
    # ================================
    # Inscriptions
    # ================================
    path('', InscriptionCreateView.as_view(), name='inscription-create'),
    path('mes-inscriptions/', ParticipantInscriptionsListView.as_view(), name='inscription-list'),
    path('<uuid:id>/', InscriptionDetailView.as_view(), name='inscription-detail'),
    path('<uuid:id>/annuler/', InscriptionCancelView.as_view(), name='inscription-cancel'),

    # ================================
    # Billets
    # ================================
    path('billets/', BilletListView.as_view(), name='billet-list'),
    path('billets/<uuid:id>/', BilletDetailView.as_view(), name='billet-detail'),

    # ================================
    # Paiements
    # ================================
    path('paiements/<uuid:id>/confirmer/', PaiementConfirmView.as_view(), name='paiement-confirmer'),
]