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

class Inscription(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('paye', 'Payé'),
        ('utilise', 'Utilisé'),
        ('annule', 'Annulé'),
        ('rembourse', 'Remboursé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="inscriptions")
    evenement = models.ForeignKey("events.Evenement", on_delete=models.CASCADE, related_name="inscriptions")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_attente")
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_inscription = models.DateTimeField(auto_now_add=True)
    reference_paiement = models.CharField(max_length=100, unique=True, blank=True)
    paiement = models.OneToOneField(Paiement, on_delete=models.SET_NULL, null=True, blank=True, related_name="inscription")

    class Meta:
        unique_together = ['participant', 'evenement']

    def generer_reference(self):
        if not self.reference_paiement:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            self.reference_paiement = f"EVT-{code}"

    def save(self, *args, **kwargs):
        self.generer_reference()
        super().save(*args, **kwargs)

class Billet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inscription = models.OneToOneField(Inscription, on_delete=models.CASCADE, related_name="billet")
    qr_code = models.ImageField(upload_to="billets_qr/", blank=True, null=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    utilise = models.BooleanField(default=False)

    def generer_qr_code(self):
        qr_data = f"billet:{self.id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        self.qr_code.save(f"billet_{self.id}.png", ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        if self.inscription.statut in ['paye', 'utilise'] and not self.qr_code:
            self.generer_qr_code()
        super().save(*args, **kwargs)

@receiver(post_save, sender=Paiement)
def synchroniser_paiement_et_inscription(sender, instance, created, **kwargs):
    try:
        inscription = instance.inscription
        if instance.statut == "confirme":
            inscription.statut = "paye"
            inscription.montant_paye = instance.montant
            inscription.save()
            Billet.objects.get_or_create(inscription=inscription)
        elif instance.statut == "rembourse":
            inscription.statut = "rembourse"
            inscription.save()
            if hasattr(inscription, 'billet'):
                inscription.billet.delete()
    except Exception as e:
        print(f"Erreur Signal: {e}")