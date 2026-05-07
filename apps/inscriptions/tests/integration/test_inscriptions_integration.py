from django.urls import reverse
import pytest
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from apps.users.models import Utilisateur
from apps.events.models import Evenement, AssignationEvenement
from apps.organisations.models import Organisation
from apps.inscriptions.models import Inscription, Billet
from apps.payments.models import Paiement
from unittest.mock import patch

@pytest.mark.django_db
@pytest.mark.integration
class InscriptionFlowIntegrationTestCase(APITestCase):
    """
    Test d'intégration couvrant le cycle de vie complet :
    1. Un participant s'inscrit à un événement (Statut: en_attente).
    2. Le paiement est confirmé (Statut: paye + Création Billet via Signal).
    3. Le participant télécharge son billet PDF.
    4. Le staff scanne le billet à l'entrée (Statut: utilise).
    """

    def setUp(self):
        # Création des acteurs
        self.owner = Utilisateur.objects.create_user(
            email="owner@test.com", password="password", nom="Owner", prenom="Test", role="proprietaire"
        )
        self.staff = Utilisateur.objects.create_user(
            email="staff@test.com", password="password", nom="Staff", prenom="Test", role="staff"
        )
        self.participant = Utilisateur.objects.create_user(
            email="participant@test.com", password="password", nom="User", prenom="Test"
        )

        # Setup Organisation et Événement
        self.org = Organisation.objects.create(nom="Big Events", proprietaire=self.owner)
        self.staff.organisation = self.org
        self.staff.save()

        self.event = Evenement.objects.create(
            titre="Festival Intégration",
            organisation=self.org,
            createur=self.owner,
            capacite_max=50,
            prix=100.0,
            statut="publie",
            date_debut=timezone.now() + timezone.timedelta(days=2)
        )

        # Assignation du staff pour le check-in
        AssignationEvenement.objects.create(staff=self.staff, evenement=self.event)

    def test_full_successful_flow(self):
        # --- ÉTAPE 1 : Inscription ---
        self.client.force_authenticate(user=self.participant)
        response_ins = self.client.post(reverse('inscription-create'), {"evenement": self.event.id})
        
        self.assertEqual(response_ins.status_code, status.HTTP_201_CREATED)
        ins_id = response_ins.data['id']
        inscription = Inscription.objects.get(id=ins_id)
        
        self.assertEqual(inscription.statut, 'en_attente')
        self.assertIsNotNone(inscription.paiement)
        self.assertEqual(inscription.paiement.statut, 'en_attente')

        # --- ÉTAPE 2 : Confirmation du Paiement (Simule le webhook Stripe / Signal) ---
        paiement = inscription.paiement
        paiement.statut = "confirme"
        paiement.save() # Ceci déclenche le signal @receiver(post_save, sender=Paiement)

        inscription.refresh_from_db()
        self.assertEqual(inscription.statut, 'paye')
        self.assertTrue(hasattr(inscription, 'billet'))
        billet = inscription.billet
        self.assertIsNotNone(billet.qr_code)

        # --- ÉTAPE 3 : Vérification accès PDF (Participant) ---
        url_pdf = reverse('billet-pdf', kwargs={'id': billet.id})
        response_pdf = self.client.get(url_pdf)
        self.assertEqual(response_pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(response_pdf['Content-Type'], 'application/pdf')

        # --- ÉTAPE 4 : Scan par le Staff (Check-in) ---
        self.client.force_authenticate(user=self.staff)
        url_scan = reverse('staff-check-in')
        
        # Le staff envoie l'ID contenu dans le QR Code
        response_scan = self.client.post(url_scan, {"billet_id": str(billet.id)})
        
        self.assertEqual(response_scan.status_code, status.HTTP_200_OK)
        self.assertEqual(response_scan.data['status'], "success")

        # Vérification finale des états en base
        billet.refresh_from_db()
        inscription.refresh_from_db()
        
        self.assertTrue(billet.utilise)
        self.assertEqual(billet.scanne_par, self.staff)
        self.assertEqual(inscription.statut, 'utilise')


    def test_integration_refund_flow(self):
        """Vérifie que l'annulation libère bien les ressources."""
        # 1. Créer le paiement d'abord
        paiement = Paiement.objects.create(
            montant=100, 
            statut="confirme", 
            external_id="pi_123",
            mode="stripe"
        )
        
        # 2. Créer l'inscription liée à ce paiement
        ins = Inscription.objects.create(
            participant=self.participant, 
            evenement=self.event, 
            statut="paye",
            paiement=paiement # On lie ici
        )
        
        # 3. Créer le billet
        Billet.objects.create(inscription=ins)

        self.client.force_authenticate(user=self.participant)
        
        with patch('stripe.Refund.create') as mock_stripe:
            # Note : vérifie que le nom de l'URL est bien 'inscription-cancel'
            response = self.client.post(reverse('inscription-cancel', kwargs={'id': str(ins.id)}))
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Inscription.objects.filter(id=ins.id).exists())