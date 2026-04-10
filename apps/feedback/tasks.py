# apps/feedback/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.events.models import Evenement
from apps.inscriptions.models import Inscription
from apps.notifications.models import Notification
from apps.feedback.models import Feedback

@shared_task
def envoyer_demandes_feedback_task():
    now = timezone.now()
    seuil_24h = now - timedelta(hours=24)
    seuil_48h = now - timedelta(hours=48)

    evenements = Evenement.objects.filter(
        statut='termine',
        date_fin__lte=seuil_24h,
        date_fin__gte=seuil_48h
    )

    count = 0

    for evt in evenements:
        inscriptions = Inscription.objects.filter(
            evenement=evt,
            statut='utilise'
        )

        for ins in inscriptions:

            # déjà envoyé email
            if getattr(ins, 'email_feedback_envoye', False):
                continue

            # déjà donné feedback
            if Feedback.objects.filter(
                participant=ins.participant,
                evenement=evt
            ).exists():
             continue

            message = (
                f"Bonjour {ins.participant.prenom}, "
                f"merci pour votre participation à '{evt.titre}'. "
                "Donnez votre avis sur votre dashboard."
            )

            Notification.objects.create(
                destinataire=ins.participant,
                sujet=f"Avis demandé : {evt.titre}",
                message=message,
                type_notification='email'
            ).envoyer()

            ins.email_feedback_envoye = True
            ins.save()

            count += 1

    return f"{count} emails envoyés"