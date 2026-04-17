import pytest
from django.db.utils import IntegrityError
from apps.feedback.models import Feedback

@pytest.mark.django_db
class TestFeedbackModels:
    def test_feedback_str_and_creation(self, create_feedback_data):
        user, event = create_feedback_data()
        fb = Feedback.objects.create(
            evenement=event, participant=user,
            note_globale=5, organisation=5, contenu=5, intervenants=5,
            lieu=5, ambiance=5, rapport_qualite_prix=5
        )
        assert fb.id is not None
        assert fb.evenement.titre == "Event Test"

    def test_unique_together_constraint(self, create_feedback_data):
        """Vérifie que la contrainte Meta unique_together fonctionne au niveau DB."""
        user, event = create_feedback_data()
        
        # Premier feedback
        Feedback.objects.create(
            evenement=event, participant=user,
            note_globale=3, organisation=3, contenu=3, intervenants=3,
            lieu=3, ambiance=3, rapport_qualite_prix=3
        )

        # Tentative du deuxième : doit lever une IntegrityError
        with pytest.raises(IntegrityError):
            Feedback.objects.create(
                evenement=event, participant=user,
                note_globale=1, organisation=1, contenu=1, intervenants=1,
                lieu=1, ambiance=1, rapport_qualite_prix=1
            )