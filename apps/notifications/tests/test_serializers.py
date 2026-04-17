# apps/notifications/tests/test_serializers.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer

Utilisateur = get_user_model()

class NotificationSerializerTestCase(TestCase):
    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            email="seria@test.com", 
            password="pass", 
            nom="Seria", 
            prenom="Test"
        )
        self.notification = Notification.objects.create(
            destinataire=self.user,
            sujet="Mise à jour",
            message="Votre billet est disponible.",
            type_notification="email",
            statut="en_attente"
        )

    def test_notification_serialization_fields(self):
        """Vérifie que les champs attendus sont présents dans le JSON."""
        serializer = NotificationSerializer(instance=self.notification)
        data = serializer.data

        # Mise à jour de la liste des champs attendus pour inclure les nouveaux champs source
        expected_fields = {
            'id', 'destinataire', 'destinataire_email', 'destinataire_nom', 
            'destinataire_prenom', 'type_notification', 'sujet', 
            'message', 'html_message', 'date_creation', 
            'date_envoi', 'statut'
        }
        
        # Cette assertion compare les clés réelles du JSON avec notre set attendu
        self.assertEqual(set(data.keys()), expected_fields)
        
        # Vérification des valeurs spécifiques
        self.assertEqual(data['sujet'], "Mise à jour")
        self.assertEqual(data['statut'], "en_attente")
        self.assertEqual(data['destinataire'], self.user.id)
        self.assertEqual(data['destinataire_email'], self.user.email)
        self.assertEqual(data['destinataire_nom'], self.user.nom)

    def test_notification_read_only_fields(self):
        """
        Vérifie que certains champs (comme date_creation) 
        ne peuvent pas être modifiés via le serializer.
        """
        data = {
            "sujet": "Nouveau Sujet",
            "statut": "envoye",
            "date_creation": "2020-01-01T00:00:00Z"
        }
        serializer = NotificationSerializer(instance=self.notification, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.notification.refresh_from_db()
        self.assertEqual(self.notification.sujet, "Nouveau Sujet")
        # La date de création ne doit PAS avoir changé malgré le payload
        self.assertNotEqual(self.notification.date_creation.year, 2020)