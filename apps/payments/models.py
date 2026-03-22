# apps/payments/models.py
from django.db import models
from django.utils import timezone
import uuid
import secrets  # Pour générer une référence sécurisée et courte

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
    
    # Correction : On autorise null=True pour éviter l'erreur de "chaîne vide" unique
    # et on garde unique=True pour la sécurité des transactions réelles.
    reference_transaction = models.CharField(
        max_length=100, 
        unique=True, 
        null=True, 
        blank=True
    )
    
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.id} ({self.statut}) - {self.montant} {self.devise}"

    def save(self, *args, **kwargs):
        # Si aucune référence n'est fournie (ex: création initiale avant paiement réel),
        # on génère une référence temporaire unique pour éviter l'IntegrityError.
        if not self.reference_transaction:
            self.reference_transaction = f"TRX-{secrets.token_hex(8).upper()}"
        super().save(*args, **kwargs)

    def confirmer(self):
        """Marque le paiement comme confirmé et met à jour la date."""
        self.statut = 'confirme'
        self.date_paiement = timezone.now()
        self.save()

    def annuler(self):
        """Annule le paiement."""
        self.statut = 'annule'
        self.save()

    def echouer(self):
        """Marque le paiement comme ayant échoué."""
        self.statut = 'echoue'
        self.save()