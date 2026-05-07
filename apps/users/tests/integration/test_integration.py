# apps/users/tests/integration/test_integration.py
import pytest

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Utilisateur
from apps.organisations.models import Organisation, Abonnement
from apps.events.models import Evenement, AssignationEvenement




@pytest.mark.django_db
@pytest.mark.integration
class TestUsersIntegration:

    def setup_method(self):
        self.client = APIClient()

        # =========================
        # BASE DATA
        # =========================
        self.owner = Utilisateur.objects.create_user(
            email="owner@test.com",
            nom="Boss",
            prenom="Owner",
            password="password123",
            role="proprietaire"
        )

        self.abonnement = Abonnement.objects.create(plan="pro")

        self.org = Organisation.objects.create(
            nom="Org",
            secteur="technologie",
            proprietaire=self.owner,
            abonnement=self.abonnement
        )

        self.owner.organisation = self.org
        self.owner.save()

    # =====================================================
    # 1. REGISTER PROPRIETAIRE
    # =====================================================
    def test_register_proprietaire_full_flow(self):
        response = self.client.post("/api/users/proprietaire/register/", {
            "nom": "Boss",
            "prenom": "Owner",
            "email": "new_owner@test.com",
            "password": "password123",
            "confirm_password": "password123",

            "nom_organisation": "Tech Corp",
            "secteur": "technologie",
            "email_contact": "contact@test.com",
            "telephone_organisation": "0102030405",
            "adresse_org": "Rue 1",
            "ville_org": "Paris",
            "pays_org": "France",
            "type_abonnement": "pro"
        }, format="json")

        assert response.status_code == 201

    def test_register_proprietaire_password_mismatch(self):
        response = self.client.post("/api/users/proprietaire/register/", {
            "nom": "Boss",
            "prenom": "Owner",
            "email": "fail@test.com",
            "password": "12345678",
            "confirm_password": "DIFF",

            "nom_organisation": "Org",
            "secteur": "technologie",
            "email_contact": "c@test.com",
            "telephone_organisation": "0102",
            "adresse_org": "Rue",
            "ville_org": "Paris",
            "pays_org": "France",
            "type_abonnement": "pro"
        }, format="json")

        assert response.status_code == 400

    # =====================================================
    # 2. LOGIN + PROFILE
    # =====================================================
    def test_login_then_access_profile(self):
        user = Utilisateur.objects.create_user(
            email="user@test.com",
            nom="Jean",
            prenom="Paul",
            password="password123"
        )

        login = self.client.post("/api/users/auth/login/", {
            "email": "user@test.com",
            "password": "password123"
        }, format="json")

        assert login.status_code == 200

        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        profile = self.client.get("/api/users/profile/")
        assert profile.status_code == 200

    def test_login_wrong_password(self):
        Utilisateur.objects.create_user(
            email="user@test.com",
            nom="Test",
            prenom="User",
            password="password123"
        )

        response = self.client.post("/api/users/auth/login/", {
            "email": "user@test.com",
            "password": "wrong"
        }, format="json")

        assert response.status_code == 401

    def test_login_inactive_user(self):
        Utilisateur.objects.create_user(
            email="inactive@test.com",
            nom="X",
            prenom="Y",
            password="password123",
            statut="inactif"
        )

        response = self.client.post("/api/users/auth/login/", {
            "email": "inactive@test.com",
            "password": "password123"
        }, format="json")

        assert response.status_code == 403

    # =====================================================
    # 3. PROPRIETAIRE -> GESTIONNAIRE
    # =====================================================
    def test_proprietaire_create_gestionnaire(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post("/api/users/gestionnaire/", {
            "email": "manager@test.com",
            "nom": "Manager",
            "prenom": "One",
            "password": "password123",
            "statut": "actif"
        }, format="json")

        assert response.status_code == 201

    def test_gestionnaire_cannot_create_gestionnaire(self):
        manager = Utilisateur.objects.create_user(
            email="manager@test.com",
            nom="M",
            prenom="G",
            password="password123",
            role="gestionnaire",
            organisation=self.org
        )

        self.client.force_authenticate(user=manager)

        response = self.client.post("/api/users/gestionnaire/", {
            "email": "fail@test.com",
            "nom": "Fail",
            "prenom": "User",
            "password": "password123"
        }, format="json")

        assert response.status_code == 403

    # =====================================================
    # 4. STAFF + EVENT
    # =====================================================
    def test_gestionnaire_create_staff_and_assign_event(self):
        manager = Utilisateur.objects.create_user(
            email="manager@test.com",
            nom="Manager",
            prenom="M",
            password="password123",
            role="gestionnaire",
            organisation=self.org
        )

        self.client.force_authenticate(user=manager)

        create_staff = self.client.post("/api/users/staff/", {
            "email": "staff@test.com",
            "nom": "Staff",
            "prenom": "S",
            "password": "password123",
            "statut": "actif"
        }, format="json")

        assert create_staff.status_code == 201

        staff = Utilisateur.objects.get(email="staff@test.com")

        event = Evenement.objects.create(
            titre="Event",
            organisation=self.org,
            date_debut="2026-01-01T10:00:00Z",
            date_fin="2026-01-01T18:00:00Z",
            capacite_max=100,
            createur=self.owner
        )

        assign = self.client.post(
            f"/api/users/staff/{staff.id}/assign_event/",
            {"event_id": event.id},
            format="json"
        )

        assert assign.status_code == 201

    def test_assign_event_without_event_id(self):
        manager = Utilisateur.objects.create_user(
            email="manager@test.com",
            nom="Manager",
            prenom="M",
            password="password123",
            role="gestionnaire",
            organisation=self.org
        )

        staff = Utilisateur.objects.create_user(
            email="staff@test.com",
            nom="Staff",
            prenom="S",
            role="staff",
            organisation=self.org,
            createur=manager
        )

        self.client.force_authenticate(user=manager)

        response = self.client.post(
            f"/api/users/staff/{staff.id}/assign_event/",
            {},
            format="json"
        )

        assert response.status_code == 400

    def test_assign_event_other_organisation(self):
        manager = Utilisateur.objects.create_user(
            email="manager@test.com",
            nom="Manager",
            prenom="M",
            password="password123",
            role="gestionnaire",
            organisation=self.org
        )

        staff = Utilisateur.objects.create_user(
            email="staff@test.com",
            nom="Staff",
            prenom="S",
            role="staff",
            organisation=self.org,
            createur=manager
        )
        other_abonnement = Abonnement.objects.create(plan="pro")

        other_org = Organisation.objects.create(
            nom="Other",
            secteur="tech",
            proprietaire=self.owner,
            abonnement=other_abonnement
       )

        

        event = Evenement.objects.create(
            titre="Hack",
            organisation=other_org,
            date_debut="2026-01-01T10:00:00Z",
            date_fin="2026-01-01T18:00:00Z",
            capacite_max=100,
            createur=self.owner
        )

        self.client.force_authenticate(user=manager)

        response = self.client.post(
            f"/api/users/staff/{staff.id}/assign_event/",
            {"event_id": event.id},
            format="json"
        )

        assert response.status_code == 404

    # =====================================================
    # 5. PROFILE
    # =====================================================
    def test_update_profile(self):
        user = Utilisateur.objects.create_user(
            email="user@test.com",
            nom="Old",
            prenom="Name",
            password="password123"
        )

        self.client.force_authenticate(user=user)

        response = self.client.put("/api/users/profile/update/", {
            "nom": "NewName",
            "ville": "Paris"
        }, format="json")

        assert response.status_code == 200

    def test_profile_requires_auth(self):
        response = self.client.get("/api/users/profile/")
        assert response.status_code == 401

    # =====================================================
    # 6. LOGOUT
    # =====================================================
    def test_logout_without_token(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post("/api/users/auth/logout/", {})
        assert response.status_code == 400

    

    def test_logout_success(self):
        refresh = RefreshToken.for_user(self.owner)

        self.client.force_authenticate(user=self.owner)

        response = self.client.post("/api/users/auth/logout/", {
            "refresh": str(refresh)
        }, format="json")

        assert response.status_code == 200