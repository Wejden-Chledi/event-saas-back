from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from apps.inscriptions.models import Inscription, Billet
from apps.events.models import Evenement
from apps.organisations.models import Organisation
from apps.notifications.models import Notification

Utilisateur = get_user_model()

class NotificationSignalTestCase(TestCase):
    def setUp(self):
        # Création des données de base
        self.owner = Utilisateur.objects.create_user(
            email="owner@test.com", password="pass", nom="Owner", prenom="Test"
        )
        self.org = Organisation.objects.create(nom="Org Test", proprietaire=self.owner)
        
        self.participant = Utilisateur.objects.create_user(
            email="parti@test.com", password="pass", nom="Parti", prenom="Test"
        )
        
        self.event = Evenement.objects.create(
            titre="Concert Test",
            organisation=self.org,
            createur=self.owner,
            prix=10.0,
            capacite_max=100
        )
        
        self.inscription = Inscription.objects.create(
            participant=self.participant,
            evenement=self.event,
            statut="paye"
        )

    @patch('apps.notifications.models.send_mail')
    def test_billet_creation_triggers_notification(self, mock_send_mail):
        """
        Vérifie que la création d'un Billet génère automatiquement 
        une Notification via le signal.
        """
        # Au début, 0 notification
        self.assertEqual(Notification.objects.count(), 0)

        # 1. Action : On crée le Billet (ce qui doit déclencher le signal)
        Billet.objects.create(inscription=self.inscription)

        # 2. Vérification : Une notification a-t-elle été créée ?
        self.assertEqual(Notification.objects.count(), 1)
        
        notif = Notification.objects.first()
        self.assertEqual(notif.destinataire, self.participant)
        self.assertIn("Concert Test", notif.sujet)
        
        # 3. Vérification : L'envoi a-t-il été tenté (le .envoyer() dans le signal) ?
        # Comme on a mocké send_mail, on vérifie si le statut est passé à 'envoye'
        # (ou 'echoue' selon si ton mock laisse passer ou non)
        self.assertIn(notif.statut, ['envoye', 'echoue'])