# apps/payments/tests/test_views.py
# apps/payments/tests/test_views.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model
from apps.inscriptions.models import Inscription
from apps.payments.models import Paiement
from apps.events.models import Evenement
from apps.organisations.models import Organisation
from decimal import Decimal
import stripe

Utilisateur = get_user_model()

class PaymentViewsTestCase(APITestCase):
    def setUp(self):
        # 1. Création de l'utilisateur
        self.user = Utilisateur.objects.create_user(
            email="pay@test.com", 
            password="pass",
            nom="Acheteur",
            prenom="Test"
        )
        
        # 2. Création de l'organisation et de l'événement
        self.org = Organisation.objects.create(nom="Org Test", proprietaire=self.user)
        self.event = Evenement.objects.create(
            titre="Event Pay", 
            organisation=self.org, 
            createur=self.user, 
            prix=Decimal("100.00"),
            capacite_max=10
        )
        
        # Authentification
        self.client.force_authenticate(user=self.user)
        
        # 3. Création du Paiement (indépendant)
        self.paiement = Paiement.objects.create(
            montant=self.event.prix,
            statut='en_attente'
        )

        # 4. Création de l'Inscription liée au paiement
        self.inscription = Inscription.objects.create(
            participant=self.user, 
            evenement=self.event,
            paiement=self.paiement
        )

    # --- TESTS DE SUCCÈS ---

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent(self, mock_stripe_create):
        """Teste la génération du clientSecret Stripe via l'API."""
        mock_stripe_create.return_value = type('obj', (object,), {
            'id': 'pi_test_123', 
            'client_secret': 'secret_un_deux_trois'
        })
        
        url = reverse('paiement-create-intent', kwargs={'inscription_id': self.inscription.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['clientSecret'], 'secret_un_deux_trois')
        
        self.paiement.refresh_from_db()
        self.assertEqual(self.paiement.external_id, 'pi_test_123')

    @patch('stripe.PaymentIntent.retrieve')
    def test_confirm_payment_success(self, mock_stripe_retrieve):
        """Teste la validation finale du paiement après succès Stripe."""
        mock_stripe_retrieve.return_value = type('obj', (object,), {'status': 'succeeded'})
        
        self.paiement.external_id = 'pi_test_123'
        self.paiement.save()

        url = reverse('paiement-confirmer', kwargs={'pk': self.paiement.id})
        response = self.client.post(url, {'external_id': 'pi_test_123'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        self.paiement.refresh_from_db()
        self.assertEqual(self.paiement.statut, 'confirme')

    def test_paiement_list_view(self):
        """Vérifie que l'utilisateur voit son historique de paiements."""
        url = reverse('paiement-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # --- TESTS D'ERREURS ET SÉCURITÉ ---

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_stripe_error(self, mock_stripe_create):
        """Teste l'échec quand Stripe est indisponible."""
        mock_stripe_create.side_effect = stripe.error.StripeError("Stripe API Down")
        
        url = reverse('paiement-create-intent', kwargs={'inscription_id': self.inscription.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # On vérifie dans 'detail' car DRF met souvent l'erreur ici par défaut
        self.assertIn('Stripe API Down', str(response.data))

    def test_confirm_payment_wrong_user(self):
        """Sécurité : Un utilisateur ne peut pas confirmer le paiement d'autrui."""
        hacker = Utilisateur.objects.create_user(
            email="hacker@test.com", password="pass", nom="Hacker", prenom="Test"
        )
        self.client.force_authenticate(user=hacker)

        url = reverse('paiement-confirmer', kwargs={'pk': self.paiement.id})
        response = self.client.post(url, {'external_id': 'pi_123'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('stripe.PaymentIntent.retrieve')
    def test_confirm_payment_failed_status(self, mock_stripe_retrieve):
        """Teste quand Stripe renvoie un statut d'échec (ex: carte refusée)."""
        mock_stripe_retrieve.return_value = type('obj', (object,), {'status': 'requires_payment_method'})
        
        self.paiement.external_id = 'pi_fail'
        self.paiement.save()

        url = reverse('paiement-confirmer', kwargs={'pk': self.paiement.id})
        response = self.client.post(url, {'external_id': 'pi_fail'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.paiement.refresh_from_db()
        self.assertNotEqual(self.paiement.statut, 'confirme')