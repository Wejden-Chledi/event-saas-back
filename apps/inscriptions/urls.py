# apps/inscriptions/urls.py
from django.urls import path
from .views import BilletPDFView
from .views import (
    InscriptionCreateView,
    ParticipantInscriptionsListView,
    InscriptionDetailView,
    BilletListView,
    BilletDetailView,
    InscriptionCancelView,
)
# On importe la vue de confirmation depuis l'application payments
from apps.payments.views import PaiementConfirmView

urlpatterns = [
    # Inscriptions
    path('', InscriptionCreateView.as_view(), name='inscription-create'),
    path('mes-inscriptions/', ParticipantInscriptionsListView.as_view(), name='inscription-list'),
    path('<uuid:id>/', InscriptionDetailView.as_view(), name='inscription-detail'),
    path('<uuid:id>/annuler/', InscriptionCancelView.as_view(), name='inscription-cancel'),

    # Billets
    path('billets/', BilletListView.as_view(), name='billet-list'),
    path('billets/<uuid:id>/', BilletDetailView.as_view(), name='billet-detail'),

    # Paiements (Route liée à l'inscription)
    path('paiements/<uuid:id>/confirmer/', PaiementConfirmView.as_view(), name='paiement-confirmer'),
    path('billets/<uuid:id>/pdf/', BilletPDFView.as_view(), name='billet-pdf'),
]