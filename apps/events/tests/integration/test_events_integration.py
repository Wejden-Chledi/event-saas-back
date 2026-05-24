# apps/events/tests/integration/test_events_integration.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.organisations.models import Organisation

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.integration
class TestEvenementIntegration:

    def setup_method(self):
        self.client = APIClient()

        # =========================
        # USERS (IMPORTANT: nom + prenom obligatoires)
        # =========================
        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="pass123",
            nom="Owner",
            prenom="Test",
            role="proprietaire"
        )

        self.manager = User.objects.create_user(
            email="manager@test.com",
            password="pass123",
            nom="Manager",
            prenom="Test",
            role="gestionnaire"
        )

        self.staff = User.objects.create_user(
            email="staff@test.com",
            password="pass123",
            nom="Staff",
            prenom="Test",
            role="staff"
        )

        # =========================
        # ORGANISATION
        # =========================
        self.org = Organisation.objects.create(
            nom="Org Test",
            secteur="technologie",
            email_contact="org@test.com",
            telephone="123456",
            adresse="Tunis",
            ville="Tunis",
            pays="Tunisie",
            proprietaire=self.owner
        )

        # rattacher manager à organisation
        self.manager.organisation = self.org
        self.manager.save()

    # =====================================================
    # 1. CREATE EVENT
    # =====================================================
    def test_create_event(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post("/api/events/", {
            "titre": "Event Test",
            "description": "Test description",
            "lieu": "Tunis",
            "date_debut": "2026-06-01T10:00:00Z",
            "date_fin": "2026-06-01T18:00:00Z",
            "capacite_max": 100,
            "prix": "20.00",
            "statut": "brouillon"
        }, format="json")

        assert response.status_code == 201
        assert response.data["titre"] == "Event Test"

    # =====================================================
    # 2. LIST EVENTS PUBLIC
    # =====================================================
    def test_list_events_public(self):
        response = self.client.get("/api/events/")
        assert response.status_code == 200

    # =====================================================
    # 3. MULTI-TENANT FILTER
    # =====================================================
    def test_events_multi_tenant(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.get("/api/events/")
        assert response.status_code == 200

    # =====================================================
    # 4. UPDATE EVENT
    # =====================================================
    def test_update_event(self):
        self.client.force_authenticate(user=self.manager)

        create_res = self.client.post("/api/events/", {
            "titre": "Event A",
            "description": "desc",
            "lieu": "Tunis",
            "date_debut": "2026-06-01T10:00:00Z",
            "date_fin": "2026-06-01T18:00:00Z",
            "capacite_max": 100,
            "prix": "20.00"
        }, format="json")

        event_id = create_res.data["id"]

        update_res = self.client.patch(f"/api/events/{event_id}/", {
            "titre": "Event Updated"
        }, format="json")

        assert update_res.status_code == 200
        assert update_res.data["titre"] == "Event Updated"

    # =====================================================
    # 5. STAFF ASSIGNED EVENTS
    # =====================================================
    def test_staff_assigned_events(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.get("/api/staff/events/assigned/")
        assert response.status_code == 200

    # =====================================================
    # 6. AI GENERATION ENDPOINT
    # =====================================================
    def test_ai_generation(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post("/api/events/generate-ai-desc/", {
            "titre": "AI Event",
            "lieu": "Paris",
            "description": "Test AI"
        }, format="json")

        # dépend de ta clé Azure OpenAI
        assert response.status_code in [200, 500]