from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification

Utilisateur = get_user_model()

class NotificationViewsTestCase(APITestCase):
    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            email="client@test.com", password="pass", nom="Client", prenom="Test"
        )
        self.other_user = Utilisateur.objects.create_user(
            email="other@test.com", password="pass", nom="Other", prenom="Test"
        )
        self.notif = Notification.objects.create(
            destinataire=self.user,
            sujet="Info",
            message="Message secret"
        )

    def test_list_notifications(self):
        """Un utilisateur ne doit voir que SES notifications."""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_detail_notification_access(self):
        """Interdire l'accès à la notification d'un autre utilisateur."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('notification-detail', kwargs={'pk': self.notif.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manual_send_view(self):
        """Tester le déclenchement manuel de l'envoi via l'API."""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-send', kwargs={'pk': self.notif.pk})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.notif.refresh_from_db()
        self.assertEqual(self.notif.statut, 'envoye')