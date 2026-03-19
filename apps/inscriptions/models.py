# apps/inscriptions/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid, random, string, qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.payments.models import Paiement
from apps.notifications.models import Notification

Utilisateur = get_user_model()


# =====================================================
# INSCRIPTION PARTICIPANT
# =====================================================
class Inscription(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="inscriptions"
    )
    evenement = models.ForeignKey(
        "events.Evenement",
        on_delete=models.CASCADE,
        related_name="inscriptions"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_attente")
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_inscription = models.DateTimeField(auto_now_add=True)
    reference_paiement = models.CharField(max_length=100, unique=True, blank=True)
    paiement = models.OneToOneField(
        Paiement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inscription"
    )

    class Meta:
        unique_together = ['participant', 'evenement']

    def __str__(self):
        return f"{self.participant} -> {self.evenement}"

    def generer_reference(self):
        if not self.reference_paiement:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            self.reference_paiement = f"EVT-{code}"

    def save(self, *args, **kwargs):
        self.generer_reference()
        super().save(*args, **kwargs)


# =====================================================
# BILLET
# =====================================================
class Billet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inscription = models.OneToOneField(
        Inscription,
        on_delete=models.CASCADE,
        related_name="billet"
    )
    qr_code = models.ImageField(upload_to="billets_qr/", blank=True, null=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    utilise = models.BooleanField(default=False)
    date_utilisation = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Billet {self.id}"

    def generer_qr_code(self):
        qr_data = f"billet:{self.id}"
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        filename = f"billet_{self.id}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.generer_qr_code()
        super().save(*args, **kwargs)


# =====================================================
# SIGNAL : après confirmation du paiement
# =====================================================
@receiver(post_save, sender=Paiement)
def confirmer_inscription_et_generer_billet(sender, instance, created, **kwargs):
    if instance.statut == "confirme":
        try:
            inscription = instance.inscription
            if inscription and inscription.statut != "paye":
                inscription.statut = "paye"
                inscription.montant_paye = instance.montant
                inscription.save()
                # Génération du billet
                billet, _ = Billet.objects.get_or_create(inscription=inscription)
                billet.save()
                # Notification email
                Notification.objects.create(
                    destinataire=inscription.participant,
                    type_notification="email",
                    sujet=f"Confirmation inscription {inscription.evenement.titre}",
                    message=f"Votre inscription à {inscription.evenement.titre} est confirmée. "
                            f"Votre billet avec QR code est disponible."
                )
        except Inscription.DoesNotExist:
            pass