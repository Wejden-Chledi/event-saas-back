# apps/events/tests/test_views.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from apps.users.models import Utilisateur
from apps.organisations.models import Organisation
from apps.events.models import Evenement

class EvenementViewSetTestCase(APITestCase):

    def setUp(self):
        # 1. Création des utilisateurs
        self.proprietaire = Utilisateur.objects.create_user(
            email="owner@event.com", nom="Owner", prenom="Test", role="proprietaire", password="pass"
        )
        self.gestionnaire = Utilisateur.objects.create_user(
            email="manager@event.com", nom="Manager", prenom="Test", role="gestionnaire", password="pass"
        )
        
        # 2. Création de l'organisation
        self.org = Organisation.objects.create(nom="Org de Test", proprietaire=self.proprietaire)
        
        # Lier les utilisateurs à l'organisation
        self.proprietaire.organisation = self.org
        self.proprietaire.save()
        self.gestionnaire.organisation = self.org
        self.gestionnaire.save()

        # 3. Création d'événements
        self.event_publie = Evenement.objects.create(
            titre="Event Public", statut="publie", organisation=self.org, 
            createur=self.proprietaire, capacite_max=100, lieu="Paris"
        )
        self.event_brouillon = Evenement.objects.create(
            titre="Event Brouillon", statut="brouillon", organisation=self.org, 
            createur=self.proprietaire, capacite_max=100, lieu="Lyon"
        )

        self.list_url = reverse('evenement-list')

    def test_list_evenements_anonyme(self):
        """Un utilisateur non connecté ne voit que les événements publiés."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['titre'], "Event Public")

    def test_list_evenements_proprietaire(self):
        """Un propriétaire voit tous les événements de son organisation."""
        self.client.force_authenticate(user=self.proprietaire)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_evenement_gestionnaire(self):
        """Vérifie qu'un gestionnaire peut créer un événement."""
        self.client.force_authenticate(user=self.gestionnaire)
        data = {
            "titre": "Nouvel Event Gestionnaire",
            "description": "Description test",
            "lieu": "Marseille",
            "capacite_max": 50,
            "prix": 10.0,
            "date_debut": (timezone.now() + timedelta(days=1)).isoformat(),
            "date_fin": (timezone.now() + timedelta(days=1, hours=2)).isoformat()
        }
        with patch('apps.events.serializers.gen_desc', return_value="IA Desc"):
            response = self.client.post(self.list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('apps.events.views.generate_event_description')
    def test_action_generate_ai_desc(self, mock_ai):
        """Vérifie l'endpoint personnalisé avec un gestionnaire autorisé."""
        self.client.force_authenticate(user=self.gestionnaire)
        mock_ai.return_value = "Superbe description générée."
        
        # Correction CRITIQUE : on s'assure que l'URL finit par un slash
        url = reverse('evenement-generate-ai-desc')
        if not url.endswith('/'):
            url += '/'
        
        data = {
            "titre": "Fête de la Musique", 
            "lieu": "Paris",
            "date_debut": (timezone.now() + timedelta(days=1)).isoformat(),
            "date_fin": (timezone.now() + timedelta(days=1, hours=2)).isoformat()
        }
        
        # follow=True permet de suivre la redirection si elle a quand même lieu
        response = self.client.post(url, data, follow=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], "Superbe description générée.")
        mock_ai.assert_called_once()

    def test_staff_assigned_events_view(self):
        """Vérifie que le staff voit les événements auxquels il est assigné."""
        staff_user = Utilisateur.objects.create_user(
            email="staff@event.com", nom="Staff", prenom="Test", role="staff", password="pass"
        )
        from apps.events.models import AssignationEvenement
        AssignationEvenement.objects.create(staff=staff_user, evenement=self.event_publie)
        
        self.client.force_authenticate(user=staff_user)
        url = reverse('staff-assigned-events')
        if not url.endswith('/'):
            url += '/'
            
        response = self.client.get(url, follow=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)