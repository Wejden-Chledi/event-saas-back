# apps/organisations/tests/test_views.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.users.models import Utilisateur
from apps.organisations.models import Organisation, Abonnement
from datetime import datetime, timedelta

class AbonnementViewsTestCase(APITestCase):

    def setUp(self):
        # 1. Création du propriétaire et de son organisation
        self.proprietaire = Utilisateur.objects.create_user(
            email="owner@test.com",
            nom="Owner",
            prenom="Test",
            role="proprietaire",
            password="password123"
        )
        
        self.abo = Abonnement.objects.create(
            plan="gratuit",
            statut="actif",
            montant=0
        )
        
        self.org = Organisation.objects.create(
            nom="Ma Startup",
            secteur="technologie",
            email_contact="contact@test.com",
            telephone="0102030405",
            proprietaire=self.proprietaire,
            abonnement=self.abo
        )

        # 2. Création d'un autre utilisateur (simple participant)
        self.autre_user = Utilisateur.objects.create_user(
            email="other@test.com",
            nom="Other",
            prenom="User",
            role="participant",
            password="password123"
        )

        self.client = APIClient()

    def test_get_abonnement_authenticated(self):
        """Vérifie qu'un utilisateur connecté peut voir l'abonnement de son organisation."""
        self.client.force_authenticate(user=self.proprietaire)
        url = reverse('get_abonnement')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan'], "gratuit")

    def test_update_abonnement_as_proprietaire(self):
        """Vérifie que le propriétaire peut changer de plan et que le prix/date sont calculés."""
        self.client.force_authenticate(user=self.proprietaire)
        url = reverse('update_abonnement')
        
        data = {"plan": "pro"}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérification des calculs automatiques de la vue
        self.abo.refresh_from_db()
        self.assertEqual(self.abo.plan, "pro")
        self.assertEqual(float(self.abo.montant), 140.0) 
        
        # Vérification de la date de fin (Pro = 90 jours selon duree_map)
        expected_date_fin = self.abo.date_debut + timedelta(days=90)
        self.assertEqual(self.abo.date_fin, expected_date_fin)

    def test_update_abonnement_permission_denied(self):
        """Vérifie qu'un utilisateur qui n'est pas propriétaire ne peut pas modifier l'abonnement."""
        self.client.force_authenticate(user=self.autre_user)
        url = reverse('update_abonnement')
        
        data = {"plan": "premium"}
        response = self.client.put(url, data, format='json')

        # Doit renvoyer 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_statut_abonnement(self):
        """Vérifie la mise à jour du statut seul."""
        self.client.force_authenticate(user=self.proprietaire)
        url = reverse('update_abonnement')
        
        data = {"statut": "suspendu"}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.abo.refresh_from_db()
        self.assertEqual(self.abo.statut, "suspendu")

    def test_update_date_fin_manuelle(self):
        """Vérifie qu'on peut forcer une date de fin spécifique via l'API."""
        self.client.force_authenticate(user=self.proprietaire)
        url = reverse('update_abonnement')
        
        nouvelle_date = (datetime.now() + timedelta(days=10)).date().isoformat()
        data = {"date_fin": nouvelle_date}
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.abo.refresh_from_db()
        self.assertEqual(self.abo.date_fin.isoformat(), nouvelle_date)

    def test_get_abonnement_no_org_error(self):
        """Vérifie l'erreur 404 si l'utilisateur n'a pas d'organisation."""
        # Correction appliquée ici : ajout de nom et prenom
        lonely_user = Utilisateur.objects.create_user(
            email="lonely@test.com", 
            password="password123", 
            role="proprietaire",
            nom="NomTest",
            prenom="PrenomTest"
        )
        self.client.force_authenticate(user=lonely_user)
        
        url = reverse('get_abonnement')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)