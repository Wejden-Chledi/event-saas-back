# apps/assistant/tests/test_views.py
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
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

        # Utilisation directe du nom défini dans apps/assistant/urls.py
        # Le nom est 'chatbot'. Si tu utilises des namespaces, ce serait 'assistant:chatbot'
        try:
            self.url = reverse('chatbot')
        except:
            # Fallback de sécurité pour le pipeline si le namespace est actif
            self.url = reverse('assistant:chatbot')

    def test_chat_access_denied_unauthenticated(self):
        """Vérifie que l'accès est refusé sans authentification."""
        response = self.client.post(self.url, {"message": "Hello"}, format='json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @patch('apps.assistant.views.get_chatbot_reply')
    def test_chat_success_authenticated(self, mock_reply):
        """Vérifie le succès de l'appel avec le bon champ 'message'."""
        mock_reply.return_value = "Ceci est une réponse de l'assistant."
        
        self.client.force_authenticate(user=self.user)
        
        # Payload correct attendu par ta vue
        payload = {"message": "Quels sont mes événements ?"}
        
        response = self.client.post(self.url, payload, format='json')
        
        # On vérifie le code 200 et que l'URL n'a pas redirigé (AttributeError fix)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['reply'] == "Ceci est une réponse de l'assistant."

    def test_chat_missing_payload(self):
        """Vérifie que l'API renvoie une erreur 400 si le 'message' est absent."""
        self.client.force_authenticate(user=self.user)
        
        # Envoi d'un body sans la clé "message"
        response = self.client.post(self.url, {"inconnu": "test"}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data