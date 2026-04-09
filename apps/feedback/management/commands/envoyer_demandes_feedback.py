# apps/feedback/management/commands/envoyer_demandes_feedback.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.events.models import Evenement
from apps.inscriptions.models import Inscription
from apps.notifications.models import Notification
from apps.feedback.models import Feedback


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

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

                # éviter doublon feedback
                if hasattr(ins, 'feedback'):
                    continue

                # éviter spam email
                if getattr(ins, 'email_feedback_envoye', False):
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

                # flag anti-spam
                ins.email_feedback_envoye = True
                ins.save()

                count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} emails envoyés"))