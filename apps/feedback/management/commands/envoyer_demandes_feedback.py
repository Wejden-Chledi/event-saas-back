# apps/feedback/management/commands/envoyer_demandes_feedback.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from apps.events.models import Evenement
from apps.inscriptions.models import Inscription
from apps.notifications.models import Notification

class Command(BaseCommand):
    help = "Envoie des emails de demande de feedback pour les événements terminés depuis 24h."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        seuil_24h = now - timedelta(hours=24)
        seuil_48h = now - timedelta(hours=48)

        # On récupère les événements terminés dans la fenêtre cible
        evenements = Evenement.objects.filter(
            statut='termine',
            date_fin__lte=seuil_24h,
            date_fin__gte=seuil_48h
        )

        count = 0

        for evt in evenements:
            # On récupère les inscriptions validées qui n'ont pas encore reçu l'email
            inscriptions = Inscription.objects.filter(
                evenement=evt,
                statut='utilise',
                email_feedback_envoye=False
            ).select_related('participant')

            for ins in inscriptions:
                # Vérifier si l'utilisateur n'a pas DEJA fait un feedback spontanément
                if hasattr(ins, 'feedback'): # Si vous avez un OneToOne ou FK inverse
                    continue

                try:
                    with transaction.atomic():
                        message = (
                            f"Bonjour {ins.participant.prenom},\n\n"
                            f"Merci pour votre participation à '{evt.titre}'. "
                            "Nous aimerions avoir votre avis pour nous améliorer !"
                            "\nDonnez votre avis ici : https://votre-site.com/dashboard/feedback"
                        )

                        # Création de la notification
                        # Note: Assurez-vous que .envoyer() est bien défini dans votre modèle Notification
                        notif = Notification.objects.create(
                            destinataire=ins.participant,
                            sujet=f"Votre avis sur : {evt.titre}",
                            message=message,
                            type_notification='email'
                        )
                        notif.envoyer()

                        # Flag pour ne plus envoyer
                        ins.email_feedback_envoye = True
                        ins.save()
                        count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erreur pour l'inscription {ins.id}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Succès : {count} demandes de feedback envoyées."))