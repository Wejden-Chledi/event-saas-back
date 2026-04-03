# apps/inscriptions/models.py
import uuid
import random
import string
import qrcode
from io import BytesIO

from django.db import models
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django.dispatch import receiver

# Imports de tes autres apps
from apps.payments.models import Paiement

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
    paiement = models.OneToOneField(
        Paiement, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="inscription"
    )

    class Meta:
        unique_together = ['participant', 'evenement']
        ordering = ['-date_inscription']

    def __str__(self):
        return f"{self.participant.email} - {self.evenement.titre} ({self.statut})"

    def generer_reference(self):
        """Génère une référence unique de type EVT-XXXXXX."""
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
    
    # --- Logique de Check-in (Staff) ---
    utilise = models.BooleanField(default=False)
    date_scan = models.DateTimeField(null=True, blank=True)
    scanne_par = models.ForeignKey(
        Utilisateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="billets_scannes"
    )

    def __str__(self):
        return f"Billet {self.id} - {self.inscription.evenement.titre}"

    def generer_qr_code(self):
        """Génère l'image du QR Code contenant l'ID du billet."""
        # On stocke l'ID simple du billet pour que le scanner puisse le traiter facilement
        qr_data = str(self.id)
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        # Le save=False est important pour éviter une boucle infinie dans le save()
        filename = f"billet_{self.id}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        # On génère le QR code uniquement si le billet est lié à une inscription payée
        # et qu'il n'a pas encore de QR code.
        if self.inscription.statut in ['paye', 'utilise'] and not self.qr_code:
            self.generer_qr_code()
        super().save(*args, **kwargs)


# =====================================================
# SIGNALS : Synchronisation avec le Paiement
# =====================================================

@receiver(post_save, sender=Paiement)
def synchroniser_paiement_et_inscription(sender, instance, created, **kwargs):
    """
    Dès qu'un paiement change de statut, on met à jour l'inscription 
    et on génère le billet si nécessaire.
    """
    try:
        # On vérifie si une inscription est liée à ce paiement
        if hasattr(instance, 'inscription'):
            inscription = instance.inscription
            
            if instance.statut == "confirme":
                inscription.statut = "paye"
                inscription.montant_paye = instance.montant
                inscription.save()
                # Création automatique du billet (le QR code sera généré dans Billet.save)
                Billet.objects.get_or_create(inscription=inscription)
                
            elif instance.statut == "rembourse":
                inscription.statut = "rembourse"
                inscription.save()
                # Optionnel : Invalider ou supprimer le billet en cas de remboursement
                if hasattr(inscription, 'billet'):
                    inscription.billet.delete()
                    
    except Exception as e:
        # En production, utilise logger.error
        print(f"Erreur Signal Paiement/Inscription: {e}")