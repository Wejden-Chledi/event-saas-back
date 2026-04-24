# apps/users/tests/test_views.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import Utilisateur
from apps.organisations.models import Organisation, Abonnement
from apps.events.models import Evenement

class UserViewsTestCase(APITestCase):

    def setUp(self):
        # 1. Création du propriétaire principal
        self.proprietaire = Utilisateur.objects.create_user(
            email="proprio@orga.com", 
            nom="Proprio", 
            prenom="Boss", 
            role="proprietaire", 
            password="password123"
        )
        
        # 2. Création de l'organisation A
        self.abonnement = Abonnement.objects.create(plan="pro", montant=140)
        self.org = Organisation.objects.create(
            nom="Org A", 
            secteur="technologie",
            proprietaire=self.proprietaire,
            abonnement=self.abonnement
        )
        
        # Lien orga
        self.proprietaire.organisation = self.org
        self.proprietaire.save()

        # 3. Création des membres de l'organisation A
        self.gestionnaire = Utilisateur.objects.create_user(
            email="gestio@orga.com", nom="Gestio", prenom="Manager", 
            role="gestionnaire", organisation=self.org, password="password123"
        )
        self.staff_existant = Utilisateur.objects.create_user(
            email="staff@orga.com", nom="Staff", prenom="Worker", 
            role="staff", organisation=self.org, password="password123", 
            createur=self.gestionnaire
        )

        # 4. Création d'une organisation B pour l'isolation
        self.autre_proprio = Utilisateur.objects.create_user(
            email="autre_p@orgb.com", nom="Autre", prenom="Proprio", 
            role="proprietaire", password="password123"
        )
        self.org_b = Organisation.objects.create(
            nom="Org B", secteur="technologie", proprietaire=self.autre_proprio
        )
        self.autre_user = Utilisateur.objects.create_user(
            email="autre@orgb.com", nom="User", prenom="B", 
            role="staff", organisation=self.org_b, password="password123"
        )

        self.login_url = reverse('login')

    # --- TESTS AUTHENTIFICATION ---

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            "email": "proprio@orga.com",
            "password": "password123"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_inactive_user(self):
        self.proprietaire.statut = "inactif"
        self.proprietaire.save()
        response = self.client.post(self.login_url, {
            "email": "proprio@orga.com",
            "password": "password123"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- TESTS GESTIONNAIRE VIEWSET ---

    def test_proprietaire_can_list_gestionnaires(self):
        self.client.force_authenticate(user=self.proprietaire)
        url = reverse('gestionnaire-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_gestionnaire_cannot_access_gestionnaire_list(self):
        self.client.force_authenticate(user=self.gestionnaire)
        url = reverse('gestionnaire-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- TESTS STAFF VIEWSET & ISOLATION ---

    def test_staff_isolation_queryset(self):
        self.client.force_authenticate(user=self.gestionnaire)
        url = reverse('staff-list')
        response = self.client.get(url)
        emails = [item['email'] for item in response.data]
        self.assertIn(self.staff_existant.email, emails)
        self.assertNotIn(self.autre_user.email, emails)

    # --- TESTS ACTIONS ---

    def test_assign_event_to_staff(self):
        """Vérifie l'assignation d'un événement au staff."""
        self.client.force_authenticate(user=self.gestionnaire)
        event = Evenement.objects.create(
            titre="Conférence Tech", 
            organisation=self.org,
            date_debut="2026-01-01T10:00:00Z",
            date_fin="2026-01-01T18:00:00Z",
            capacite_max=100,
            createur=self.proprietaire  # <--- Ajouté ici
        )
        url = reverse('staff-assign-event', args=[self.staff_existant.id])
        response = self.client.post(url, {"event_id": event.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_assign_event_wrong_organisation_fails(self):
        """Un gestionnaire ne peut pas assigner un événement d'une autre orga."""
        self.client.force_authenticate(user=self.gestionnaire)
        event_autre = Evenement.objects.create(
            titre="Secret Event", 
            organisation=self.org_b,
            date_debut="2026-01-01T10:00:00Z",
            date_fin="2026-01-01T18:00:00Z",
            capacite_max=50,
            createur=self.autre_proprio  # <--- Ajouté ici
        )
        url = reverse('staff-assign-event', args=[self.staff_existant.id])
        response = self.client.post(url, {"event_id": event_autre.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- TESTS PROFIL ---

    def test_profile_view_authenticated(self):
        self.client.force_authenticate(user=self.staff_existant)
        url = reverse('user-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.staff_existant.email)