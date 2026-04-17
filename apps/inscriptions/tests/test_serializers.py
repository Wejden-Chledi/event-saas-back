from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.users.models import Utilisateur
from apps.events.models import Evenement
from apps.organisations.models import Organisation
from apps.inscriptions.models import Inscription
from apps.inscriptions.serializers import InscriptionCreateSerializer
from unittest.mock import MagicMock, patch

class InscriptionSerializerTestCase(TestCase):
    def setUp(self):
        # Correction ici aussi : ajout de nom et prenom
        self.user = Utilisateur.objects.create_user(
            email="user@test.com", password="pass", nom="User", prenom="Test"
        )
        self.owner = Utilisateur.objects.create_user(
            email="owner@test.com", password="pass", nom="Owner", prenom="Test"
        )
        self.org = Organisation.objects.create(nom="Org Test", proprietaire=self.owner)
        
        self.event = Evenement.objects.create(
            titre="Workshop", 
            organisation=self.org, 
            createur=self.owner,
            capacite_max=2,
            prix=10.0,
            statut="publie",
            date_debut=timezone.now() + timezone.timedelta(days=1),
            date_fin=timezone.now() + timezone.timedelta(days=1, hours=2)
        )
        
        self.context = {"request": MagicMock(user=self.user)}

    def test_validate_already_registered(self):
        """Vérifie qu'on ne peut pas s'inscrire deux fois."""
        Inscription.objects.create(participant=self.user, evenement=self.event, statut="en_attente")
        
        serializer = InscriptionCreateSerializer(data={"evenement": self.event.id}, context=self.context)
        with self.assertRaises(ValidationError) as cm:
            serializer.is_valid(raise_exception=True)
        self.assertIn("déjà une inscription", str(cm.exception))

    @patch.object(Evenement, 'est_complet', return_value=True)
    def test_validate_event_full(self, mock_complet):
        """Vérifie qu'on ne peut pas s'inscrire si l'événement est complet."""
        serializer = InscriptionCreateSerializer(data={"evenement": self.event.id}, context=self.context)
        with self.assertRaises(ValidationError) as cm:
            serializer.is_valid(raise_exception=True)
        self.assertIn("complet", str(cm.exception))

    def test_create_inscription_and_paiement(self):
        """Vérifie la création atomique Inscription + Paiement."""
        serializer = InscriptionCreateSerializer(data={"evenement": self.event.id}, context=self.context)
        self.assertTrue(serializer.is_valid())
        
        inscription = serializer.save()
        self.assertEqual(inscription.participant, self.user)
        self.assertIsNotNone(inscription.paiement)
        self.assertEqual(inscription.paiement.statut, 'en_attente')

    def test_validate_event_not_published(self):
        """Vérifie le refus si l'événement n'est pas publié."""
        self.event.statut = "brouillon"
        self.event.save()
        
        serializer = InscriptionCreateSerializer(data={"evenement": self.event.id}, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("pas ouvert aux inscriptions", str(serializer.errors['non_field_errors'][0]))