# apps/inscriptions/urls.py
from django.urls import path
from .views import (
    InscriptionCreateView,
    ParticipantInscriptionsListView,
    InscriptionDetailView,
    InscriptionCancelView,
    BilletListView,
    BilletDetailView,
    BilletPDFView
)

urlpatterns = [
    # --- Inscriptions ---
    # Liste globale des inscriptions de l'utilisateur connecté et création
    path('', ParticipantInscriptionsListView.as_view(), name='inscription-list'),
    path('create/', InscriptionCreateView.as_view(), name='inscription-create'),
    
    # Détails et actions spécifiques
    path('<uuid:id>/', InscriptionDetailView.as_view(), name='inscription-detail'),
    path('<uuid:id>/annuler/', InscriptionCancelView.as_view(), name='inscription-cancel'),

    # --- Billets ---
    path('billets/', BilletListView.as_view(), name='billet-list'),
    path('billets/<uuid:id>/', BilletDetailView.as_view(), name='billet-detail'),
    path('billets/<uuid:id>/pdf/', BilletPDFView.as_view(), name='billet-pdf'),
]