# apps/events/views/feedback_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.events.models import Feedback


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def feedback_event(request, event_id):

    feedbacks = Feedback.objects.filter(
        evenement_id=event_id,
        evenement__organisation=request.user.gestionnaire_profile.organisation
    )

    data = []

    for f in feedbacks:
        data.append({
            "participant": f.participant.email,
            "note": f.note,
            "commentaire": f.commentaire
        })

    return Response(data)