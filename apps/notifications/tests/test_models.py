from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from unittest.mock import patch
from apps.notifications.models import Notification

Utilisateur = get_user_model()

class NotificationModelTestCase(TestCase):
    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            email="notif@test.com", 
            password="pass", 
            nom="User", 
            prenom="Test"
        )

    def test_notification_creation(self):
        """Vérifie la création et le statut par défaut."""
        notif = Notification.objects.create(
            destinataire=self.user,
            sujet="Test",
            message="Contenu de test"
        )
        self.assertEqual(notif.statut, 'en_attente')
        self.assertEqual(str(notif), f"email -> {self.user.email} [en_attente]")

    def test_envoyer_email_success(self):
        """Vérifie que l'envoi d'email fonctionne (Mocké)."""
        notif = Notification.objects.create(
            destinataire=self.user,
            sujet="Bienvenue",
            message="Bonjour !",
            html_message="<h1>Bonjour !</h1>"
        )
        
        success = notif.envoyer()
        
        self.assertTrue(success)
        self.assertEqual(notif.statut, 'envoye')
        self.assertIsNotNone(notif.date_envoi)
        # Vérifie que Django a bien "tenté" d'envoyer 1 email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Bienvenue")

    @patch('apps.notifications.models.send_mail')
    def test_envoyer_email_failure(self, mock_send_mail):
        """Vérifie la gestion d'erreur si le serveur SMTP crash."""
        mock_send_mail.side_effect = Exception("SMTP Error")
        
        notif = Notification.objects.create(
            destinataire=self.user,
            message="Test erreur"
        )
        
        success = notif.envoyer()
        
        self.assertFalse(success)
        self.assertEqual(notif.statut, 'echoue')