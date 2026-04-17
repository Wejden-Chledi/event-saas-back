# apps/events/tests/test_services.py
from django.test import SimpleTestCase
from unittest.mock import patch, MagicMock
from apps.events.data_prep_service import EventDataPreparer
from apps.events.ai_service import generate_event_description

class EventDataPreparerTestCase(SimpleTestCase):
    """
    Tests unitaires pour la logique de préparation des données.
    On utilise SimpleTestCase car on n'a pas besoin de base de données ici.
    """

    def setUp(self):
        self.preparer = EventDataPreparer()

    def test_clean_text(self):
        """Vérifie le nettoyage : minuscules, ponctuation et stop words."""
        raw_text = "Le festival de Musique à Paris !!!"
        # 'le', 'de', 'à' (si présent dans stop_words) devraient disparaître
        cleaned = self.preparer.clean_text(raw_text)
        
        self.assertIn("festival", cleaned)
        self.assertIn("musique", cleaned)
        self.assertIn("paris", cleaned)
        self.assertNotIn("Le", cleaned) # Test minuscule
        self.assertNotIn("!!!", cleaned) # Test ponctuation

    def test_categorize_event_tech(self):
        """Vérifie la détection de la catégorie technologie."""
        data = {
            "titre": "Workshop sur l'IA et le Digital",
            "description": "Apprendre à coder des logiciels."
        }
        category = self.preparer.categorize_event(data)
        self.assertEqual(category, "technologie")

    def test_categorize_event_sport(self):
        """Vérifie la détection de la catégorie sport."""
        data = {
            "titre": "Marathon de la ville",
            "description": "Une compétition pour les athlètes."
        }
        category = self.preparer.categorize_event(data)
        self.assertEqual(category, "sport")

    def test_detect_language_fr(self):
        """Vérifie la détection du français."""
        text = "Ceci est un événement magnifique à Paris."
        self.assertEqual(self.preparer.detect_language(text), "fr")

    def test_detect_language_en(self):
        """Vérifie la détection de l'anglais."""
        text = "This is a wonderful international conference."
        self.assertEqual(self.preparer.detect_language(text), "en")

    def test_build_structured_prompt_en(self):
        """Vérifie que le prompt est généré en anglais si le titre est en anglais."""
        data = {
            "titre": "Annual Tech Summit",
            "description": "Gathering of experts",
            "lieu": "London",
            "prix": 100,
            "capacite_max": 200,
            "date_debut": "2026-05-01",
            "date_fin": "2026-05-02"
        }
        prompt = self.preparer.build_structured_prompt(data)
        self.assertIn("Title: Annual Tech Summit", prompt)
        self.assertIn("Generate a professional", prompt) # Texte anglais


class AIServiceTestCase(SimpleTestCase):
    """
    Tests pour l'interaction avec Azure OpenAI.
    On mocke le client pour ne pas faire d'appels réels.
    """

    @patch('apps.events.ai_service.get_openai_client')
    def test_generate_event_description_success(self, mock_get_client):
        """Vérifie que le service extrait correctement la réponse du client Azure."""
        # Simulation de la structure de réponse complexe d'OpenAI
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Description générée avec succès"))
        ]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = generate_event_description("Mon super prompt")
        
        self.assertEqual(result, "Description générée avec succès")
        mock_client.chat.completions.create.assert_called_once()