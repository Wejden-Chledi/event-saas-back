# apps/notifications/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

Utilisateur = get_user_model()

class Notification(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('envoye', 'Envoyé'),
        ('echoue', 'Échoué'),
    ]

    destinataire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES, default='email')
    sujet = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_envoi = models.DateTimeField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    def __str__(self):
        return f"{self.type_notification} -> {self.destinataire.email} [{self.statut}]"

    def envoyer(self):
        try:
            # ici tu peux mettre send_mail ou autre service
            self.statut = 'envoye'
            self.date_envoi = timezone.now()
            self.save()
        except Exception:
            self.statut = 'echoue'
            self.save()