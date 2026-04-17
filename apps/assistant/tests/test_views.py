import pytest
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import patch

# Récupération du modèle Utilisateur personnalisé
User = get_user_model()

@pytest.mark.django_db
class TestAssistantViews:

    def setup_method(self):
        """Initialisation de l'environnement de test."""
        self.client = APIClient()
        
        # Création de l'utilisateur
        self.user = User.objects.create_user(
            email="tester@eventora.com",
            nom="Test",
            prenom="Assistant",
            password="password123"
        )

        # Résolution de l'URL
        possible_names = ['assistant-chat', 'assistant:assistant-chat', 'assistant:chat']
        self.url = None
        for name in possible_names:
            try:
                self.url = reverse(name)
                break
            except NoReverseMatch:
                continue
        
        if not self.url:
            self.url = "/api/assistant/chat/"

    def test_chat_access_denied_unauthenticated(self):
        """Vérifie que l'accès est refusé sans authentification."""
        # On utilise "message" ici aussi par cohérence
        response = self.client.post(self.url, {"message": "Hello"}, format='json')
        assert response.status_code in [401, 403]

    @patch('apps.assistant.views.get_chatbot_reply')
    def test_chat_success_authenticated(self, mock_reply):
        """Vérifie le succès de l'appel avec le bon champ 'message'."""
        mock_reply.return_value = "Ceci est une réponse de l'assistant."
        
        self.client.force_authenticate(user=self.user)
        
        # CORRECTION : La clé doit être "message" et non "query"
        payload = {"message": "Quels sont mes événements ?"}
        
        response = self.client.post(self.url, payload, format='json')
        
        assert response.status_code == 200
        assert response.data['reply'] == "Ceci est une réponse de l'assistant."

    def test_chat_missing_payload(self):
        """Vérifie que l'API renvoie une erreur 400 si le 'message' est absent."""
        self.client.force_authenticate(user=self.user)
        
        # Envoi d'un body vide ou sans la clé "message"
        response = self.client.post(self.url, {"inconnu": "test"}, format='json')
        
        assert response.status_code == 400
        assert "error" in response.data