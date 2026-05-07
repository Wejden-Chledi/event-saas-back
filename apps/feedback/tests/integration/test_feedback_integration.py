import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from decimal import Decimal

from apps.users.models import Utilisateur
from apps.events.models import Evenement
from apps.organisations.models import Organisation
from apps.inscriptions.models import Inscription
from apps.feedback.models import Feedback, RapportIAEvenement

class FeedbackIntegrationTestCase(APITestCase):
    def setUp(self):
        # FIX: Ajout de nom et prenom obligatoires
        self.participant = Utilisateur.objects.create_user(
            email="participant@test.com", 
            password="password123",
            nom="Acheteur",
            prenom="Jean"
        )
        self.organisateur = Utilisateur.objects.create_user(
            email="admin@event.com", 
            password="password123",
            nom="Org",
            prenom="Boss"
        )

        self.org = Organisation.objects.create(nom="IA Events", proprietaire=self.organisateur)
        self.event = Evenement.objects.create(
            titre="Conférence IA",
            organisation=self.org,
            createur=self.organisateur,
            prix=Decimal("0.00"),
            capacite_max=100,
            statut="publie"
        )

        # Inscription par défaut (non scannée)
        self.inscription = Inscription.objects.create(
            participant=self.participant,
            evenement=self.event,
            statut='paye'
        )

    def test_feedback_denied_if_not_scanned(self):
        """Vérifie le blocage si le billet n'est pas au statut 'utilise'."""
        self.client.force_authenticate(user=self.participant)
        url = reverse('feedback-list')
        
        data = {
            "evenement": self.event.id,
            "organisation": 5, "contenu": 5, "intervenants": 5,
            "lieu": 5, "ambiance": 5, "rapport_qualite_prix": 5,
            "commentaire": "Super !"
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Seuls les participants ayant scanné leur billet", str(response.data))

    @patch('apps.feedback.serializers.analyser_sentiment_avis')
    def test_feedback_success_and_calculation(self, mock_ai):
        """Vérifie la création et le calcul automatique de la note globale."""
        self.inscription.statut = 'utilise'
        self.inscription.save()
        mock_ai.return_value = "Positif"

        self.client.force_authenticate(user=self.participant)
        url = reverse('feedback-list')
        
        data = {
            "evenement": self.event.id,
            "organisation": 5, "contenu": 3, "intervenants": 4,
            "lieu": 2, "ambiance": 5, "rapport_qualite_prix": 5,
            "commentaire": "Top"
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Moyenne : 24 / 6 = 4
        self.assertEqual(response.data['note_globale'], 4)

    def test_prevent_duplicate_feedback(self):
        """Vérifie l'impossibilité de voter deux fois."""
        self.inscription.statut = 'utilise'
        self.inscription.save()
        
        Feedback.objects.create(
            evenement=self.event, participant=self.participant,
            organisation=5, contenu=5, intervenants=5, lieu=5, ambiance=5, 
            rapport_qualite_prix=5, note_globale=5
        )

        self.client.force_authenticate(user=self.participant)
        url = reverse('feedback-list')
        response = self.client.post(url, {"evenement": self.event.id, "organisation": 5})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.feedback.services.get_openai_client')
    def test_generate_ia_report_service(self, mock_openai):
        """Teste la génération du rapport IA via le service."""
        from apps.feedback.services import generer_rapport_ia_evenement
        
        Feedback.objects.create(
            evenement=self.event, participant=self.participant,
            organisation=4, contenu=4, intervenants=4, lieu=4, ambiance=4, 
            rapport_qualite_prix=4, note_globale=4, commentaire="Génial"
        )

        mock_response = mock_openai.return_value.chat.completions.create.return_value
        mock_response.choices[0].message.content = '{"analyse": "Succès", "decision": "Rien"}'

        result = generer_rapport_ia_evenement(self.event.id)
        self.assertEqual(result, "Succès")
        self.assertTrue(RapportIAEvenement.objects.filter(evenement=self.event).exists())

    @patch('apps.feedback.services.get_openai_client')
    def test_generer_analyse_globale_organisation(self, mock_openai):
        """Couverture Services : Teste l'analyse transversale de l'organisation."""
        from apps.feedback.services import generer_analyse_globale_organisation
        
        # On simule une réponse de l'IA pour l'organisation
        mock_response = mock_openai.return_value.chat.completions.create.return_value
        mock_response.choices[0].message.content = "Analyse globale : Excellente performance sur tous les événements."

        # Appel du service avec l'objet organisation
        result = generer_analyse_globale_organisation(self.org)
        
        self.assertIn("Excellente performance", result)
        from apps.feedback.models import RapportGlobalOrganisation
        self.assertTrue(RapportGlobalOrganisation.objects.filter(organisation=self.org).exists())