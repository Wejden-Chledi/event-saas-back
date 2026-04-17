# apps/events/tests/test_serializers.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from apps.users.models import Utilisateur
from apps.organisations.models import Organisation
from apps.events.models import Evenement
from apps.events.serializers import EvenementSerializer

class EvenementSerializerTestCase(TestCase):

    def setUp(self):
        self.proprietaire = Utilisateur.objects.create_user(
            email="owner@test.com", nom="Owner", prenom="Test", role="proprietaire", password="pass"
        )
        self.org = Organisation.objects.create(nom="Org Test", proprietaire=self.proprietaire)
        
        # Dates au format ISO pour le sérialiseur
        self.debut = timezone.now() + timedelta(days=1)
        self.fin = self.debut + timedelta(hours=2)

        self.base_data = {
            "titre": "Nouvel Event",
            "description": "Une description obligatoire",
            "lieu": "Paris",
            "capacite_max": 50,
            "prix": 20.0,
            "date_debut": self.debut.isoformat(),
            "date_fin": self.fin.isoformat(),
            "organisation": self.org.id,
            "createur": self.proprietaire.id
        }

    def test_validate_dates_error(self):
        """Vérifie que la date de fin doit être après le début."""
        invalid_data = self.base_data.copy()
        invalid_data["date_fin"] = (self.debut - timedelta(hours=1)).isoformat()
        
        serializer = EvenementSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("date_fin", serializer.errors)

    @patch("apps.events.serializers.gen_desc")
    def test_create_with_ai_description(self, mock_gen_desc):
        """Vérifie que l'IA génère la description si elle est vide."""
        mock_gen_desc.return_value = "Description générée par IA"
        
        data_ai = self.base_data.copy()
        data_ai["description"] = "" # On déclenche l'IA
        
        serializer = EvenementSerializer(data=data_ai)
        # Note : Si is_valid échoue, assurez-vous que 'description' a blank=True dans models.py
        self.assertTrue(serializer.is_valid(), f"Erreurs: {serializer.errors}")
        
        event = serializer.save(createur=self.proprietaire, organisation=self.org)
        self.assertEqual(event.description, "Description générée par IA")

    def test_read_only_fields(self):
        """Vérifie que createur et organisation ne sont pas modifiables."""
        serializer = EvenementSerializer(data=self.base_data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn("createur", serializer.validated_data)
        self.assertNotIn("organisation", serializer.validated_data)

    def test_update_capacity_constraint(self):
        """Vérifie la validation de capacité sans planter sur les inscriptions inexistantes."""
        # Création d'un événement réel
        event = Evenement.objects.create(
            titre="Event Existant",
            description="Desc",
            lieu="Lieu",
            capacite_max=10,
            organisation=self.org,
            createur=self.proprietaire,
            date_debut=self.debut,
            date_fin=self.fin
        )

        # On Mock la relation inscriptions pour éviter l'erreur si l'app n'est pas là
        with patch.object(Evenement, 'inscriptions') as mock_inscriptions:
            # On simule 0 inscription payée
            mock_inscriptions.filter.return_value.count.return_value = 0
            
            data = {"capacite_max": 5}
            # partial=True est crucial pour un PATCH
            serializer = EvenementSerializer(instance=event, data=data, partial=True)
            
            self.assertTrue(serializer.is_valid(), f"Erreurs: {serializer.errors}")
            updated_event = serializer.save()
            self.assertEqual(updated_event.capacite_max, 5)