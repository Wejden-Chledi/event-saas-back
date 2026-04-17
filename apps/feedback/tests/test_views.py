import pytest
from unittest.mock import patch
from rest_framework import status
from apps.feedback.models import Feedback

@pytest.mark.django_db
class TestFeedbackViews:

    def test_post_feedback_success(self, auth_client, create_feedback_data):
        user, event = create_feedback_data()
        client = auth_client(user)

        data = {
            "evenement": event.id,
            "organisation": 5, "contenu": 4, "intervenants": 5,
            "lieu": 3, "ambiance": 4, "rapport_qualite_prix": 5,
            "commentaire": "Très bonne expérience"
        }

        # On mock l'appel IA dans le serializer create
        with patch('apps.feedback.serializers.analyser_sentiment_avis', return_value="Positif"):
            response = client.post("/api/feedback/avis/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['note_globale'] == 4  # Moyenne de (5+4+5+3+4+5)/6 = 4.33 -> 4
        assert response.data['sentiment_ia'] == "Positif"

    def test_post_feedback_denied_if_not_scanned(self, auth_client, create_user, create_event):
        user = create_user(email="notscanned@test.com")
        event = create_event("Event Locked")
        client = auth_client(user)

        data = {
            "evenement": event.id,
            "organisation": 5, "contenu": 5, "intervenants": 5,
            "lieu": 5, "ambiance": 5, "rapport_qualite_prix": 5
        }
        
        response = client.post("/api/feedback/avis/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Seuls les participants ayant scanné leur billet" in str(response.data)

    def test_action_a_noter(self, auth_client, create_feedback_data):
        user, event = create_feedback_data()
        event.statut = 'termine' # L'événement doit être terminé
        event.save()
        
        client = auth_client(user)
        response = client.get("/api/feedback/avis/a_noter/")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == event.id