# ============================================================================
# Fichier : apps/assistant/urls.py
#
# Ce fichier contient la configuration des routes URL liées
# au module Assistant intelligent Eventora.
#
# Il définit :
#
#   - L'accès à l'API chatbot permettant aux utilisateurs authentifiés
#     d'envoyer des questions et recevoir des réponses générées par l'IA.
#
# Ces routes assurent la communication entre le frontend et la vue
# ChatbotView.
# ============================================================================


from django.urls import path

from .views import ChatbotView


# ============================================================================
# ROUTES ASSISTANT
# ============================================================================

urlpatterns = [

    # Endpoint principal du chatbot
    # Permet d'envoyer un message utilisateur au service IA
    # Exemple :
    # POST /api/assistant/chat/
    path(
        'chat/',
        ChatbotView.as_view(),
        name='chatbot'
    ),
]