import pytest
import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from apps.users.models import Utilisateur
from apps.events.models import Evenement
from apps.organisations.models import Organisation
from django.utils import timezone

class AssistantIntegrationTestCase(APITestCase):
    def setUp(self):
        # 1. Création de l'utilisateur
        self.user = Utilisateur.objects.create_user(
            email="user@assistant.com",
            password="password123",
            nom="Test",
            prenom="User"
        )
        self.client.force_authenticate(user=self.user)
        
        # 2. Création de l'organisation (avec son propriétaire)
        self.org = Organisation.objects.create(
            nom="Org de Test", 
            proprietaire=self.user
        )
        
        # 3. Création de l'événement test (avec son créateur)
        self.event = Evenement.objects.create(
            organisation=self.org,
            createur=self.user,  # <--- Ajout crucial ici
            titre="Atelier Python Avancé",
            description="Apprendre Django et l'IA",
            lieu="Paris",
            date_debut=timezone.now() + timezone.timedelta(days=5),
            capacite_max=20,
            prix=0,
            statut="publie"
        )
        self.url = reverse('chatbot')

    @patch('apps.assistant.services.get_openai_client')
    @patch('os.getenv', return_value="gpt-4")
    def test_chatbot_full_flow(self, mock_env, mock_get_client):
        """
        Vérifie le cycle complet : 
        Question -> Detection Langue -> Tool Call -> DB Search -> Réponse Finale.
        """
        # Configuration du Mock Azure OpenAI
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Étape 1 : Simulation du choix de l'IA d'appeler l'outil (get_events)
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_abc_123"
        mock_tool_call.function.name = "get_events"
        mock_tool_call.function.arguments = json.dumps({"query_term": "Paris"})
        
        mock_first_msg = MagicMock()
        mock_first_msg.tool_calls = [mock_tool_call]
        mock_first_msg.content = None
        
        mock_first_res = MagicMock()
        mock_first_res.choices = [MagicMock(message=mock_first_msg)]
        
        # Étape 2 : Simulation de la réponse finale de l'IA
        mock_final_msg = MagicMock()
        mock_final_msg.content = "Il y a un atelier Python à Paris avec 20 places."
        mock_final_msg.tool_calls = None
        
        mock_final_res = MagicMock()
        mock_final_res.choices = [MagicMock(message=mock_final_msg)]
        
        # On définit les retours successifs
        mock_client.chat.completions.create.side_effect = [mock_first_res, mock_final_res]

        # Appel API
        payload = {"message": "Quels sont les événements à Paris ?"}
        response = self.client.post(self.url, payload, format='json')

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("atelier Python", response.data['reply'])
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)

    def test_search_events_db_logic(self):
        """Vérifie que la fonction DB filtre bien les résultats par lieu ou titre."""
        from apps.assistant.services import search_events_in_db
        
        # Test recherche par lieu (Paris)
        res_json = search_events_in_db("Paris")
        res_data = json.loads(res_json)
        self.assertEqual(len(res_data), 1)
        self.assertEqual(res_data[0]['title'], "Atelier Python Avancé")

        # Test recherche inexistante
        res_empty = search_events_in_db("Marseille")
        self.assertEqual(res_empty, "Aucun événement trouvé / No events found.")

    def test_detect_language_logic(self):
        """Vérifie la robustesse de la détection FR/EN."""
        from apps.assistant.services import detect_language
        
        # Test mots-clés anglais
        self.assertEqual(detect_language("How many events?"), "en")
        # Test détection naturelle français
        self.assertEqual(detect_language("C'est quand le prochain atelier ?"), "fr")