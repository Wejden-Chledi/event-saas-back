import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.users.models import Utilisateur
# On s'assure d'importer AssignationEvenement depuis la bonne app
from apps.events.models import Evenement, AssignationEvenement
from apps.organisations.models import Organisation
from apps.inscriptions.models import Inscription, Billet
from apps.payments.models import Paiement

class InscriptionViewsTestCase(APITestCase):

    def setUp(self):
        # 1. Création des utilisateurs avec nom/prenom obligatoires
        self.participant = Utilisateur.objects.create_user(
            email="part@test.com", password="pass", nom="Part", prenom="Test"
        )
        self.owner = Utilisateur.objects.create_user(
            email="owner@test.com", password="pass", role="proprietaire", nom="Owner", prenom="Test"
        )
        self.staff = Utilisateur.objects.create_user(
            email="staff@test.com", password="pass", role="staff", nom="Staff", prenom="Test"
        )

        # 2. Organisation et Événement
        self.org = Organisation.objects.create(nom="Org Test", proprietaire=self.owner)
        self.owner.organisation = self.org
        self.owner.save()
        
        # Rattachement du staff à l'organisation
        self.staff.organisation = self.org
        self.staff.save()

        self.event = Evenement.objects.create(
            titre="Event Test",
            organisation=self.org,
            createur=self.owner,
            capacite_max=100,
            prix=20.0,
            statut="publie",
            date_debut=timezone.now() + timezone.timedelta(days=1)
        )

        # 3. Assignation du staff (SANS l'argument 'role' qui causait l'erreur)
        AssignationEvenement.objects.create(
            staff=self.staff, 
            evenement=self.event
        )

    def test_create_inscription_success(self):
        self.client.force_authenticate(user=self.participant)
        url = reverse('inscription-create')
        data = {"evenement": self.event.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_participant_inscriptions(self):
        Inscription.objects.create(participant=self.participant, evenement=self.event)
        self.client.force_authenticate(user=self.participant)
        url = reverse('inscription-list')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    @patch('stripe.Refund.create')
    def test_cancel_inscription_with_refund(self, mock_refund):
        paiement = Paiement.objects.create(montant=20.0, statut='confirme', external_id="pi_test")
        ins = Inscription.objects.create(
            participant=self.participant, 
            evenement=self.event, 
            statut="paye",
            paiement=paiement
        )
        self.client.force_authenticate(user=self.participant)
        url = reverse('inscription-cancel', kwargs={'id': ins.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Inscription.objects.count(), 0)

    def test_staff_checkin_success(self):
        ins = Inscription.objects.create(participant=self.participant, evenement=self.event, statut="paye")
        billet = Billet.objects.create(inscription=ins)
        self.client.force_authenticate(user=self.staff)
        url = reverse('staff-check-in')
        response = self.client.post(url, {"billet_id": str(billet.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        billet.refresh_from_db()
        self.assertTrue(billet.utilise)

    def test_staff_checkin_wrong_org(self):
        # Un staff d'une autre organisation
        other_owner = Utilisateur.objects.create_user(email="other@test.com", password="pass", nom="O", prenom="T")
        other_org = Organisation.objects.create(nom="Other Org", proprietaire=other_owner)
        other_staff = Utilisateur.objects.create_user(email="badstaff@test.com", password="pass", nom="S", prenom="T")
        other_staff.organisation = other_org
        other_staff.save()

        ins = Inscription.objects.create(participant=self.participant, evenement=self.event, statut="paye")
        billet = Billet.objects.create(inscription=ins)

        self.client.force_authenticate(user=other_staff)
        url = reverse('staff-check-in')
        response = self.client.post(url, {"billet_id": str(billet.id)})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('reportlab.pdfgen.canvas.Canvas.save')
    @patch('reportlab.pdfgen.canvas.Canvas.drawImage')
    def test_download_billet_pdf(self, mock_img, mock_save):
        ins = Inscription.objects.create(participant=self.participant, evenement=self.event, statut="paye")
        billet = Billet.objects.create(inscription=ins)
        self.client.force_authenticate(user=self.participant)
        url = reverse('billet-pdf', kwargs={'id': billet.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_staff_event_participants_list(self):
        Inscription.objects.create(participant=self.participant, evenement=self.event)
        self.client.force_authenticate(user=self.staff)
        url = reverse('staff-event-participants', kwargs={'event_id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_cancel_already_used_billet_fails(self):
        """Interdire l'annulation d'un billet déjà scanné."""
        ins = Inscription.objects.create(participant=self.participant, evenement=self.event, statut="utilise")
        self.client.force_authenticate(user=self.participant)
        url = reverse('inscription-cancel', kwargs={'id': ins.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], "Impossible d'annuler un billet déjà utilisé.")

    def test_staff_checkin_already_scanned(self):
        """Vérifier l'erreur si le billet est déjà utilisé."""
        ins = Inscription.objects.create(participant=self.participant, evenement=self.event, statut="paye")
        billet = Billet.objects.create(inscription=ins, utilise=True, date_scan=timezone.now())
        
        self.client.force_authenticate(user=self.staff)
        url = reverse('staff-check-in')
        response = self.client.post(url, {"billet_id": str(billet.id)})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Alerte", response.data['error'])

    def test_event_participants_dashboard_filter(self):
        """Tester le filtre event_id du dashboard."""
        Inscription.objects.create(participant=self.participant, evenement=self.event)
        self.client.force_authenticate(user=self.owner) # Créateur de l'event
        url = reverse('participants-list')
        
        # Test avec filtre correct
        response = self.client.get(f"{url}?event_id={self.event.id}")
        self.assertEqual(len(response.data), 1)
        
        # Test avec filtre "all"
        response = self.client.get(f"{url}?event_id=all")
        self.assertEqual(len(response.data), 1)    