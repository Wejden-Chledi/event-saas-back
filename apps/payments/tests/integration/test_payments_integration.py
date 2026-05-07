import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from decimal import Decimal

from apps.users.models import Utilisateur
from apps.organisations.models import Organisation
from apps.events.models import Evenement
from apps.inscriptions.models import Inscription, Billet
from apps.payments.models import Paiement

class PaymentsIntegrationTestCase(APITestCase):
    def setUp(self):
        """Configuration initiale pour un cycle complet de paiement."""
        # 1. Création du participant (Acheteur)
        self.user = Utilisateur.objects.create_user(
            email="buyer@integration.com",
            password="password123",
            nom="Acheteur",
            prenom="Jean"
        )
        
        # 2. Création de l'organisateur
        self.organisateur = Utilisateur.objects.create_user(
            email="org@test.com", 
            password="password123",
            nom="Organisateur",
            prenom="Directeur"
        )
        
        # 3. Création de l'organisation et de l'événement
        self.org = Organisation.objects.create(
            nom="Integration Org", 
            proprietaire=self.organisateur
        )
        self.event = Evenement.objects.create(
            titre="Grand Gala d'Intégration",
            organisation=self.org,
            createur=self.organisateur,
            prix=Decimal("75.00"),
            capacite_max=100,
            statut="publie"
        )

        # Authentification du participant
        self.client.force_authenticate(user=self.user)

    @patch('stripe.PaymentIntent.retrieve')
    @patch('stripe.PaymentIntent.create')
    def test_full_payment_to_ticket_flow(self, mock_stripe_create, mock_stripe_retrieve):
        """
        PARCOURS CRITIQUE :
        1. Inscription à l'événement
        2. Génération du Client Secret Stripe
        3. Confirmation du paiement
        4. Vérification de la création automatique du Billet
        """
        
        # --- ÉTAPE 1 : Création de l'inscription via l'API ---
        inscription_url = reverse('inscription-create')
        data_inscription = {'evenement': self.event.id}
        resp_ins = self.client.post(inscription_url, data_inscription, format='json')
        
        self.assertEqual(resp_ins.status_code, status.HTTP_201_CREATED)
        inscription_id = resp_ins.data['id']
        
        # Récupération du paiement associé créé en base par ton backend
        inscription_obj = Inscription.objects.get(id=inscription_id)
        paiement_id = inscription_obj.paiement.id

        # --- ÉTAPE 2 : Création de l'intention Stripe (PaymentIntent) ---
        mock_stripe_create.return_value = type('obj', (object,), {
            'id': 'pi_integration_123',
            'client_secret': 'seti_secret_999'
        })

        intent_url = reverse('paiement-create-intent', kwargs={'inscription_id': inscription_id})
        resp_intent = self.client.post(intent_url)

        self.assertEqual(resp_intent.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_intent.data['clientSecret'], 'seti_secret_999')

        # --- ÉTAPE 3 : Confirmation du paiement (Succès Stripe) ---
        # On simule que Stripe renvoie un statut 'succeeded'
        mock_stripe_retrieve.return_value = type('obj', (object,), {'status': 'succeeded'})

        confirm_url = reverse('paiement-confirmer', kwargs={'pk': paiement_id})
        resp_confirm = self.client.post(confirm_url, {'external_id': 'pi_integration_123'})

        self.assertEqual(resp_confirm.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_confirm.data['status'], 'success')

        # --- ÉTAPE 4 : Vérification des impacts métiers finaux ---
        # Le paiement doit être 'confirme'
        paiement_db = Paiement.objects.get(id=paiement_id)
        self.assertEqual(paiement_db.statut, 'confirme')

        # L'inscription doit être 'paye'
        inscription_obj.refresh_from_db()
        self.assertEqual(inscription_obj.statut, 'paye')

        # UN BILLET DOIT EXISTER (C'est le test ultime de ton intégration)
        billet_exists = Billet.objects.filter(inscription=inscription_obj).exists()
        self.assertTrue(billet_exists, "Le billet n'a pas été généré après confirmation du paiement.")

    def test_payment_unauthorized_access(self):
        """Vérifie qu'un participant ne peut pas confirmer le paiement d'un autre."""
        autre_user = Utilisateur.objects.create_user(
            email="hacker@test.com", 
            password="password123",
            nom="Hacker",
            prenom="Bad"
        )
        
        # Création d'une inscription pour cet autre utilisateur
        paiement_autre = Paiement.objects.create(montant=Decimal("50.00"), statut='en_attente')
        Inscription.objects.create(
            participant=autre_user, 
            evenement=self.event, 
            paiement=paiement_autre
        )

        # Tentative de confirmation par Jean (self.user) sur le paiement du Hacker
        url = reverse('paiement-confirmer', kwargs={'pk': paiement_autre.id})
        response = self.client.post(url, {'external_id': 'pi_fake'})

        # Doit renvoyer 404 car la vue filtre le queryset par request.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)