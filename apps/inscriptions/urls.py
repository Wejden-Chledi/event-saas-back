# apps/inscriptions/urls.py
from django.urls import path
from .views import (
    # Vues Participants
    BilletDetailView,
    InscriptionCreateView,
    ParticipantInscriptionsListView,
    InscriptionDetailView,
    InscriptionCancelView,
    BilletListView,
    BilletPDFView,
    
    # Vues Staff (Check-in)
    StaffBilletCheckInView,
    StaffEventParticipantsListView
)

urlpatterns = [
    # =====================================================
    # ESPACE PARTICIPANTS (Client-facing)
    # =====================================================
    
    # Gestion des inscriptions
    path('', ParticipantInscriptionsListView.as_view(), name='inscription-list'),
    path('create/', InscriptionCreateView.as_view(), name='inscription-create'),
    
    # Détails et annulation (Utilise l'ID de l'inscription)
    path('<uuid:id>/', InscriptionDetailView.as_view(), name='inscription-detail'),
    path('<uuid:id>/annuler/', InscriptionCancelView.as_view(), name='inscription-cancel'),

    # Accès aux billets et téléchargement PDF
    path('billets/', BilletListView.as_view(), name='billet-list'),

    path('billets/<uuid:id>/', BilletDetailView.as_view(), name='billet-detail'),
    
    # Note : BilletDetailView est retirée car non définie dans tes vues actuelles.
    # On privilégie le PDF ou la liste globale.
    path('billets/<uuid:id>/pdf/', BilletPDFView.as_view(), name='billet-pdf'),

    # =====================================================
    # ESPACE STAFF (Scanner & Gestion d'entrée)
    # =====================================================
    
    # Validation d'un billet via scan QR Code (POST billet_id)
    path('staff/check-in/', StaffBilletCheckInView.as_view(), name='staff-check-in'),
    
    # Liste des inscrits pour un événement (recherche manuelle/liste d'émargement)
    # Exemple : /api/inscriptions/staff/participants-list/?event_id=UUID
    path('staff/participants-list/', StaffEventParticipantsListView.as_view(), name='staff-participants-list'),
]