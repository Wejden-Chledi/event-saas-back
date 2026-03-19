# apps/payments/models.py
from django.db import models
from django.utils import timezone
import uuid

class Paiement(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('annule', 'Annulé'),
        ('echoue', 'Échoué'),
    ]

    MODE_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('autre', 'Autre'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=10, default="EUR")
    date_paiement = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='stripe')
    reference_transaction = models.CharField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.statut} - {self.montant} {self.devise}"

    def confirmer(self):
        self.statut = 'confirme'
        self.date_paiement = timezone.now()
        self.save()

    def annuler(self):
        self.statut = 'annule'
        self.save()

    def echouer(self):
        self.statut = 'echoue'
        self.save()