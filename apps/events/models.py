from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import random
import string
from django.utils import timezone

from apps.organisations.models import Organisation

Utilisateur = get_user_model()


# =====================================================
# EVENEMENT
# =====================================================

class Evenement(models.Model):

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('publie', 'Publié'),
        ('annule', 'Annulé'),
        ('termine', 'Terminé'),
    ]

    id = models.BigAutoField(primary_key=True)

    titre = models.CharField(max_length=200)
    description = models.TextField()

    lieu = models.CharField(max_length=200)

    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField(default=timezone.now)

    capacite_max = models.PositiveIntegerField()

    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='brouillon'
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="evenements"
    )

    createur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="evenements_crees"
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    date_update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_debut']

    def __str__(self):
        return self.titre

    # places restantes
    def places_disponibles(self):
        total = self.inscriptions.filter(statut="paye").count()
        return max(0, self.capacite_max - total)

    # vérifier si complet
    def est_complet(self):
        return self.places_disponibles() <= 0

    # publier événement
    def publier(self):
        self.statut = "publie"
        self.save()

    # annuler
    def annuler(self):
        self.statut = "annule"
        self.save()


# =====================================================
# STAFF
# =====================================================

class Staff(models.Model):

    ROLE_CHOICES = [
        ('staff', 'Staff')
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    password = models.CharField(max_length=128)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='staff'
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='actif'
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="staff"
    )

    telephone = models.CharField(max_length=20, blank=True, null=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def set_password(self, password):
        from django.contrib.auth.hashers import make_password
        self.password = make_password(password)

    def check_password(self, password):
        from django.contrib.auth.hashers import check_password
        return check_password(password, self.password)


# =====================================================
# ASSIGNATION STAFF EVENEMENT
# =====================================================

class AssignationEvenement(models.Model):

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="assignations"
    )

    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name="staff_assignes"
    )

    date_assignation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['staff', 'evenement']

    def __str__(self):
        return f"{self.staff} -> {self.evenement}"


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
        Evenement,
        on_delete=models.CASCADE,
        related_name="inscriptions"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en_attente"
    )

    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    date_inscription = models.DateTimeField(auto_now_add=True)

    reference_paiement = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )

    class Meta:
        unique_together = ['participant', 'evenement']

    def __str__(self):
        return f"{self.participant} - {self.evenement}"

    def generer_reference(self):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.reference_paiement = f"EVT-{code}"



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

    code = models.CharField(max_length=20, unique=True)

    date_emission = models.DateTimeField(auto_now_add=True)
    utilise = models.BooleanField(default=False)
    date_utilisation = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code

    def generer_code_unique(self):
        """Génère un code aléatoire unique pour le billet."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            if not Billet.objects.filter(code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generer_code_unique()
        super().save(*args, **kwargs)
# =====================================================
# FEEDBACK
# =====================================================

class Feedback(models.Model):

    participant = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE
    )

    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    note = models.IntegerField()

    commentaire = models.TextField(blank=True)

    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["participant", "evenement"]

    def __str__(self):
        return f"{self.participant} - {self.evenement}"


# =====================================================
# PHOTO EVENEMENT
# =====================================================

class EventPhoto(models.Model):

    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name="photos"
    )

    image = models.ImageField(upload_to="events/")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.name