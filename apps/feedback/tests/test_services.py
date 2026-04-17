import pytest
import os
from unittest.mock import patch, MagicMock
from apps.feedback.models import Feedback, RapportIAEvenement
from apps.feedback.services import generer_rapport_ia_evenement

@pytest.mark.django_db
class TestFeedbackServices:

    # On patch 'get_openai_client' ET l'appel direct à OpenAI pour être blindé
    @patch('apps.feedback.services.get_openai_client')
    def test_generer_rapport_ia_evenement(self, mock_get_client, create_feedback_data):
        """Vérifie la génération du rapport en simulant entièrement la réponse IA."""
        user, event = create_feedback_data()
    
        # 1. Création du feedback
        Feedback.objects.create(
            evenement=event, 
            participant=user,
            organisation=5, 
            contenu=5, 
            intervenants=5, 
            lieu=5,
            ambiance=5, 
            rapport_qualite_prix=5, 
            note_globale=5,
            sentiment_ia="Positif",
            commentaire="L'événement était incroyable."
        )

        # 2. Mock du client et de la réponse
        mock_openai = MagicMock()
        mock_get_client.return_value = mock_openai
        
        # On simule la structure exacte de la réponse Azure OpenAI
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"analyse": "Succès global", "decision": "Continuer"}'))
        ]
        mock_openai.chat.completions.create.return_value = mock_response

        # 3. Appel du service (on s'assure que l'environnement est mocké aussi)
        with patch.dict(os.environ, {"AZURE_OPENAI_DEPLOYMENT": "test-deployment"}):
            rapport_contenu = generer_rapport_ia_evenement(event.id)

        # 4. Vérifications
        assert rapport_contenu == "Succès global"
        
        rapport_obj = RapportIAEvenement.objects.get(evenement=event)
        assert rapport_obj.resume_ia == "Succès global"
        assert rapport_obj.aide_decision == "Continuer"

    def test_generer_rapport_sans_feedback(self, create_event):
        """Vérifie le message si aucun feedback n'est présent."""
        event = create_event("Event Vide")
        rapport = generer_rapport_ia_evenement(event.id)
        assert rapport == "Pas assez de feedbacks pour générer un rapport."