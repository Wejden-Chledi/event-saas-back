# apps/inscriptions/urls.py
from django.urls import path
from .views import (
    # Vues Participants
    InscriptionCreateView,
    ParticipantInscriptionsListView,
    InscriptionDetailView,
    InscriptionCancelView,
    BilletListView,
    BilletDetailView,
    BilletPDFView,
    
    # Vues Staff
    StaffBilletCheckInView,
    StaffEventParticipantsListView
)

urlpatterns = [
    # 1. ROUTES STATIQUES (Toujours en haut)
    path('', ParticipantInscriptionsListView.as_view(), name='inscription-list'),
    path('create/', InscriptionCreateView.as_view(), name='inscription-create'),
    path('billets/', BilletListView.as_view(), name='billet-list'),
    
    # 2. ROUTES STAFF (Préfixées par staff/, donc pas de conflit)
    path('staff/check-in/', StaffBilletCheckInView.as_view(), name='staff-check-in'),
    path('staff/participants-list/', StaffEventParticipantsListView.as_view(), name='staff-participants-list'),

    # 3. ROUTES BILLETS SPÉCIFIQUES
    # On les place AVANT <uuid:id>/ pour éviter que l'ID de l'inscription n'intercepte l'URL
    path('billets/<uuid:id>/', BilletDetailView.as_view(), name='billet-detail'),
    path('billets/<uuid:id>/pdf/', BilletPDFView.as_view(), name='billet-pdf'),

    # 4. ROUTES GÉNÉRIQUES (À mettre en dernier)
    # Cette route est très "gourmande", elle attrape tout ce qui ressemble à un UUID
    path('<uuid:id>/', InscriptionDetailView.as_view(), name='inscription-detail'),
    path('<uuid:id>/annuler/', InscriptionCancelView.as_view(), name='inscription-cancel'),
]