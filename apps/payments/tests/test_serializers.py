from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.payments.models import Paiement
from apps.payments.serializers import PaiementSerializer
from apps.inscriptions.models import Inscription
from apps.events.models import Evenement
from apps.organisations.models import Organisation
from decimal import Decimal

Utilisateur = get_user_model()

class PaiementSerializerTestCase(TestCase):
    def setUp(self):
        # 1. Création de l'environnement nécessaire
        self.user = Utilisateur.objects.create_user(
            email="testpay@example.com", 
            password="password123",
            nom="Acheteur",
            prenom="Test"
        )
        self.org = Organisation.objects.create(
            nom="Ma Super Org", 
            proprietaire=self.user
        )
        self.event = Evenement.objects.create(
            titre="Conférence Django 2026",
            organisation=self.org,
            createur=self.user,
            prix=Decimal("99.00"),
            capacite_max=50
        )
        
        # 2. Création de l'inscription (qui génère souvent le paiement via signal)
        self.inscription = Inscription.objects.create(
            participant=self.user,
            evenement=self.event,
            statut='en_attente'
        )
        
        # 3. Récupération ou création du paiement lié
        # Si ton signal post_save sur Inscription crée déjà le paiement, on le récupère
        self.paiement = getattr(self.inscription, 'paiement', None)
        if not self.paiement:
            self.paiement = Paiement.objects.create(
                montant=self.event.prix,
                statut='en_attente'
            )
            # Lien manuel si nécessaire (selon ta logique de OneToOneField)
            self.inscription.paiement = self.paiement
            self.inscription.save()

    def test_serializer_output(self):
        """Vérifie que le JSON contient les données du paiement et de l'événement lié."""
        serializer = PaiementSerializer(instance=self.paiement)
        data = serializer.data

        # Vérification des champs de base
        self.assertEqual(Decimal(data['montant']), Decimal("99.00"))
        self.assertEqual(data['statut'], 'en_attente')
        self.assertEqual(data['statut_label'], 'En attente')
        
        # Vérification des champs calculés (source="inscription.evenement...")
        self.assertEqual(data['evenement_titre'], "Conférence Django 2026")
        self.assertIn('reference_transaction', data)
        self.assertTrue(data['reference_transaction'].startswith("PAY-"))