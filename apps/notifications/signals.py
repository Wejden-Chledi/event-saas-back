# apps/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.inscriptions.models import Billet  # Import croisé vers inscriptions
from .models import Notification

@receiver(post_save, sender=Billet)
def notifier_nouveau_billet(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            destinataire=instance.inscription.participant,
            sujet=f"Votre billet pour {instance.inscription.evenement.titre}",
            message=f"Félicitations ! Votre billet est prêt. ID: {instance.id}",
            type_notification='email'
        ).envoyer()