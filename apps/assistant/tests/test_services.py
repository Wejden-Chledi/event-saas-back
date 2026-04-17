import pytest
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.assistant.services import detect_language, search_events_in_db
from apps.events.models import Evenement
from apps.organisations.models import Organisation 

Utilisateur = get_user_model()

@pytest.mark.django_db
class TestAssistantServices:

    # --- Tests Détection de Langue ---
    @pytest.mark.parametrize("text, expected_lang", [
        ("Quels sont les événements ?", "fr"),
        ("Are there any events available?", "en"),
        ("How many seats are left?", "en"),
        ("C'est quoi cette conférence ?", "fr"), 
    ])
    def test_detect_language(self, text, expected_lang):
        assert detect_language(text) == expected_lang

    # --- Test Recherche DB ---
    def test_search_events_success(self):
        # 1. Création de l'utilisateur (Propriétaire et Créateur)
        user = Utilisateur.objects.create_user(
            email="test@eventora.com",
            nom="Doe",
            prenom="John",
            password="password123"
        )

        # 2. Création de l'organisation avec son propriétaire obligatoire
        org = Organisation.objects.create(
            nom="Eventora Org",
            proprietaire=user  # Ajout du propriétaire pour corriger l'IntegrityError
        )

        # 3. Création de l'événement
        Evenement.objects.create(
            titre="Conférence React",
            description="Apprendre React",
            lieu="Paris",
            capacite_max=100,      
            prix=15.00,
            organisation=org,      
            createur=user,         
            statut='publie',
            date_debut=timezone.now()
        )
        
        # 4. Exécution du test
        result = search_events_in_db("React")
        data = json.loads(result)
        
        assert len(data) == 1
        assert data[0]['title'] == "Conférence React"

    def test_search_events_no_results(self):
        result = search_events_in_db("Inexistant")
        assert "found" in result.lower() or "trouvé" in result.lower()