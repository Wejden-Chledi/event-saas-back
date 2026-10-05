# apps/inscriptions/urls.py


# Gestion des routes API de l'application inscriptions
from django.urls import path



# Import des différentes vues utilisées par les URLs
from .views import (

    # ==============================
    # Vues Participants
    # ==============================

    # Création d'une inscription avant paiement
    InscriptionCreateView,

    # Liste des inscriptions du participant connecté
    ParticipantInscriptionsListView,

    # Détail d'une inscription spécifique
    InscriptionDetailView,

    # Annulation d'une inscription
    InscriptionCancelView,


    # Liste des billets du participant
    BilletListView,

    # Détail d'un billet
    BilletDetailView,

    # Génération du billet en PDF
    BilletPDFView,



    # ==============================
    # Vues Staff
    # ==============================

    # Validation d'entrée par scan QR Code
    StaffBilletCheckInView,

    # Liste des participants d'un événement
    EventParticipantsListView,

    # Liste des participants visible par le staff
    StaffEventParticipantsView

)





# =====================================================
# ROUTES INSCRIPTIONS
# =====================================================
#
# Organisation des URLs :
#
# /inscriptions/
#
# Participant :
#   - consulter ses inscriptions
#   - créer une inscription
#   - consulter ses billets
#
# Staff :
#   - scanner un billet
#   - consulter les participants
#
# Important :
# Les routes spécifiques doivent être placées
# avant les routes avec paramètres dynamiques.
# =====================================================



urlpatterns = [



    # =================================================
    # 1. ROUTES PARTICIPANTS
    # =================================================



    # GET :
    # Retourne toutes les inscriptions
    # du participant connecté.
    path(
        '',
        ParticipantInscriptionsListView.as_view(),
        name='inscription-list'
    ),



    # POST :
    # Création d'une nouvelle inscription.
    #
    # Création automatique :
    # - paiement en attente
    # - inscription associée
    path(
        'create/',
        InscriptionCreateView.as_view(),
        name='inscription-create'
    ),



    # GET :
    # Retourne les billets payés
    # du participant connecté.
    path(
        'billets/',
        BilletListView.as_view(),
        name='billet-list'
    ),






    # =================================================
    # 2. ROUTES STAFF
    # =================================================



    # GET :
    # Affiche les participants
    # d'un événement précis.
    #
    # Exemple :
    # /event/5/participants/
    path(
        'event/<int:event_id>/participants/',
        StaffEventParticipantsView.as_view(),
        name='staff-event-participants'
    ),



    # POST :
    # Scan du QR Code par le staff.
    #
    # Vérifie :
    # - validité du billet
    # - organisation
    # - assignation du staff
    # - utilisation précédente
    path(
        'staff/check-in/',
        StaffBilletCheckInView.as_view(),
        name='staff-check-in'
    ),



    # GET :
    # Liste des participants liés
    # aux événements du gestionnaire.
    path(
        'participants-list/',
        EventParticipantsListView.as_view(),
        name='participants-list'
    ),






    # =================================================
    # 3. ROUTES BILLETS
    # =================================================



    # GET :
    # Retourne les informations
    # d'un billet précis.
    #
    # Placée avant <uuid:id>
    # pour éviter un conflit de route.
    path(
        'billets/<uuid:id>/',
        BilletDetailView.as_view(),
        name='billet-detail'
    ),



    # GET :
    # Génère et retourne le billet PDF.
    path(
        'billets/<uuid:id>/pdf/',
        BilletPDFView.as_view(),
        name='billet-pdf'
    ),






    # =================================================
    # 4. ROUTES GENERIQUES
    # =================================================
    #
    # Ces routes utilisent un UUID.
    #
    # Elles doivent toujours être placées
    # en dernier car elles peuvent intercepter
    # plusieurs URLs.
    # =================================================



    # GET :
    # Détail d'une inscription.
    path(
        '<uuid:id>/',
        InscriptionDetailView.as_view(),
        name='inscription-detail'
    ),



    # POST :
    # Annulation d'une inscription.
    path(
        '<uuid:id>/annuler/',
        InscriptionCancelView.as_view(),
        name='inscription-cancel'
    ),

]