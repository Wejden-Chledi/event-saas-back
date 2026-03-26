# apps/payments/models.py
from django.db import models
from django.utils import timezone
import uuid
import secrets

class Paiement(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('annule', 'Annulé'),
        ('echoue', 'Échoué'),
        ('rembourse', 'Remboursé'),
    ]

    MODE_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('virement', 'Virement'),
        ('autre', 'Autre'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=10, default="EUR")
    date_paiement = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='stripe')
    
    # Référence interne (générée par nous)
    reference_transaction = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # ID externe (ex: pi_123... de Stripe)
    external_id = models.CharField(max_length=255, null=True, blank=True)
    
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.reference_transaction} ({self.statut}) - {self.montant} {self.devise}"

    def save(self, *args, **kwargs):
        if not self.reference_transaction:
            self.reference_transaction = f"PAY-{secrets.token_hex(6).upper()}"
        super().save(*args, **kwargs)

    def confirmer(self, external_id=None):
        """Action de confirmation déclenchant le signal post_save"""
        self.statut = 'confirme'
        if external_id:
            self.external_id = external_id
        self.date_paiement = timezone.now()
        self.save()

    def annuler(self):
        self.statut = 'annule'
        self.save()

    def echouer(self):
        self.statut = 'echoue'
        self.save()

    def rembourser(self): 
        """Action de remboursement"""
        self.statut = 'rembourse'
        self.save()   