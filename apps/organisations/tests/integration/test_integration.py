import pytest
from rest_framework.test import APIClient
from apps.users.models import Utilisateur
from apps.organisations.models import Organisation, Abonnement


@pytest.mark.django_db
class TestOrganisationIntegration:

    def setup_method(self):
        self.client = APIClient()

        # Propriétaire
        self.owner = Utilisateur.objects.create_user(
            email="owner@test.com",
            nom="Owner",
            prenom="Test",
            password="password123",
            role="proprietaire"
        )

    # ==========================
    # 1. CREATE ORGANISATION
    # ==========================
    def test_create_organisation(self):

        self.client.force_authenticate(user=self.owner)

        response = self.client.post("/api/organisations/", {
            "nom": "Tech Corp",
            "secteur": "technologie",
            "description": "test org",
            "email_contact": "contact@test.com",
            "telephone": "123456",
            "adresse": "Rue 1",
            "ville": "Paris",
            "pays": "France",
            "site_web": "https://test.com",
            "abonnement": {
                "plan": "pro",
                "montant": 140
            }
        }, format="json")

        assert response.status_code == 201

        org = Organisation.objects.get(nom="Tech Corp")
        assert org.proprietaire == self.owner
        assert org.abonnement.plan == "pro"

    # ==========================
    # 2. GET ORGANISATION (ME)
    # ==========================
    def test_get_my_organisation(self):

        abonnement = Abonnement.objects.create(plan="pro")

        org = Organisation.objects.create(
            nom="My Org",
            secteur="technologie",
            email_contact="a@a.com",
            telephone="123",
            adresse="Rue",
            proprietaire=self.owner,
            abonnement=abonnement
        )

        self.owner.organisation = org
        self.owner.save()

        self.client.force_authenticate(user=self.owner)

        response = self.client.get("/api/organisations/me/")

        assert response.status_code == 200
        assert response.data["nom"] == "My Org"

    # ==========================
    # 3. UPDATE ORGANISATION
    # ==========================
    def test_update_organisation(self):

        abonnement = Abonnement.objects.create(plan="pro")

        org = Organisation.objects.create(
            nom="Old Name",
            secteur="technologie",
            email_contact="a@a.com",
            telephone="123",
            adresse="Rue",
            proprietaire=self.owner,
            abonnement=abonnement
        )

        self.client.force_authenticate(user=self.owner)

        response = self.client.patch("/api/organisations/me/", {
            "nom": "New Name"
        })

        assert response.status_code == 200

        org.refresh_from_db()
        assert org.nom == "New Name"

    # ==========================
    # 4. STATS ENDPOINT
    # ==========================
    def test_organisation_stats(self):

        abonnement = Abonnement.objects.create(plan="pro")

        org = Organisation.objects.create(
            nom="Stats Org",
            secteur="tech",
            email_contact="a@a.com",
            telephone="123",
            adresse="Rue",
            proprietaire=self.owner,
            abonnement=abonnement
        )

        self.owner.organisation = org
        self.owner.save()

        self.client.force_authenticate(user=self.owner)

        response = self.client.get("/api/organisations/stats/")

        assert response.status_code == 200
        assert isinstance(response.data, list)

    # ==========================
    # 5. PERMISSION TEST
    # ==========================
    def test_gestionnaire_cannot_create_org(self):

        manager = Utilisateur.objects.create_user(
            email="manager@test.com",
            nom="M",
            prenom="M",
            password="password123",
            role="gestionnaire"
        )

        self.client.force_authenticate(user=manager)

        response = self.client.post("/api/organisations/", {
            "nom": "Fail Org",
            "secteur": "tech",
            "email_contact": "x@test.com",
            "telephone": "000",
            "adresse": "Rue"
        })

        assert response.status_code in [403, 401]