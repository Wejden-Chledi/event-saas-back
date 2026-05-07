import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core import mail
from unittest.mock import patch
from decimal import Decimal

from apps.users.models import Utilisateur
from apps.events.models import Evenement
from apps.organisations.models import Organisation
from apps.inscriptions.models import Inscription, Billet
from apps.notifications.models import Notification

class NotificationsIntegrationTestCase(APITestCase):
    def setUp(self):
        # 1. Création des utilisateurs
        self.user = Utilisateur.objects.create_user(
            email="notif_user@test.com",
            password="password123",
            nom="User",
            prenom="Test"
        )
        self.org_owner = Utilisateur.objects.create_user(
            email="owner@test.com",
            password="password123",
            nom="Owner",
            prenom="Boss"
        )

        # 2. Setup Organisation et Événement
        self.org = Organisation.objects.create(nom="Notif Org", proprietaire=self.org_owner)
        self.event = Evenement.objects.create(
            titre="Event Notifications",
            organisation=self.org,
            createur=self.org_owner,
            prix=Decimal("10.00"),
            capacite_max=50,
            statut="publie"
        )

        # 3. Création d'une inscription de base
        self.inscription = Inscription.objects.create(
            participant=self.user,
            evenement=self.event,
            statut='paye'
        )

    def test_signal_notification_on_billet_creation(self):
        """Vérifie que la création d'un billet déclenche bien une notification."""
        # On vérifie qu'il n'y a pas de notification au début
        self.assertEqual(Notification.objects.count(), 0)

        # Action : Créer un billet (déclenche le signal notifier_nouveau_billet)
        Billet.objects.create(inscription=self.inscription)

        # Vérification 1 : Une notification a été créée en DB
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.destinataire, self.user)
        self.assertEqual(notif.type_notification, 'email')
        
        # Vérification 2 : L'email a été envoyé (Django place les emails dans mail.outbox durant les tests)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.event.titre, mail.outbox[0].subject)
        self.assertEqual(notif.statut, 'envoye')

    def test_notification_api_access(self):
        """Vérifie que l'utilisateur peut voir ses notifications via l'API."""
        # Création manuelle d'une notification
        notif = Notification.objects.create(
            destinataire=self.user,
            sujet="Test API",
            message="Contenu de test",
            statut='en_attente'
        )

        self.client.force_authenticate(user=self.user)
        
        # Test List View
        url_list = reverse('notification-list')
        response = self.client.get(url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sujet'], "Test API")

        # Test Detail View
        url_detail = reverse('notification-detail', kwargs={'pk': notif.id})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(notif.message, response.data['message'])

    def test_manual_send_via_api(self):
        """Vérifie le déclenchement manuel de l'envoi via l'API."""
        notif = Notification.objects.create(
            destinataire=self.user,
            sujet="Envoi Manuel",
            message="Test manuel",
            statut='en_attente'
        )

        self.client.force_authenticate(user=self.user)
        url_send = reverse('notification-send', kwargs={'pk': notif.id})
        
        # On vide la boite mail de test pour être sûr
        mail.outbox = []

        response = self.client.post(url_send)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        
        notif.refresh_from_db()
        self.assertEqual(notif.statut, 'envoye')

    def test_security_access_other_notification(self):
        """Un utilisateur ne doit pas pouvoir voir ou renvoyer la notification d'un autre."""
        autre_user = Utilisateur.objects.create_user(
            email="hacker@test.com", password="password", nom="H", prenom="B"
        )
        notif_privee = Notification.objects.create(
            destinataire=autre_user, sujet="Secret", message="Privé"
        )

        self.client.force_authenticate(user=self.user) # On s'identifie en tant que 'user'
        
        # Test Detail (doit être 404)
        url = reverse('notification-detail', kwargs={'pk': notif_privee.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test Send (doit être 404)
        url_send = reverse('notification-send', kwargs={'pk': notif_privee.id})
        response = self.client.post(url_send)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_serializer_validation_invalid_type(self):
        """Couverture Serializer : Teste le validateur de type de notification."""
        from apps.notifications.serializers import NotificationSerializer
        
        data = {
            "destinataire": self.user.id,
            "type_notification": "pigeon_voyageur",  # Type invalide
            "message": "Hello"
        }
        serializer = NotificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('type_notification', serializer.errors)

    @patch('apps.notifications.models.send_mail')
    def test_notification_send_failure_logic(self, mock_send_mail):
        """Couverture Model : Teste le bloc 'except' en cas d'erreur d'envoi."""
        # On simule une erreur réseau/SMTP
        mock_send_mail.side_effect = Exception("SMTP Error")
        
        notif = Notification.objects.create(
            destinataire=self.user,
            sujet="Test Failure",
            message="Will fail"
        )
        
        success = notif.envoyer()
        
        self.assertFalse(success)
        self.assertEqual(notif.statut, 'echoue')