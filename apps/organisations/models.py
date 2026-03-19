# apps/organisations/models.py

from django.db import models
from django.utils import timezone
from apps.users.models import Utilisateur


# =====================================================
# ABONNEMENT 
# =====================================================


class Abonnement(models.Model):

    PLAN_CHOICES = [
        ('gratuit', 'Gratuit'),
        ('basique', 'Basique'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('expire', 'Expiré'),
    ]

    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='gratuit')

    date_debut = models.DateField(default=timezone.now)
    date_fin = models.DateField(null=True, blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')

    # ✅ AJOUT IMPORTANT
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plan} - {self.statut}"

    def verifier_expiration(self):
        if self.date_fin and timezone.now().date() > self.date_fin:
            self.statut = 'expire'
            self.save()

# =====================================================
# ORGANISATION (COEUR DU SAAS)
# =====================================================

class Organisation(models.Model):
    """
    Organisation = client principal du SaaS.

    🔥 Elle regroupe :
    - propriétaire
    - gestionnaires
    - staff
    - événements
    - abonnement

    👉 Multi-tenant system (clé du SaaS)
    """

    SECTEUR_CHOICES = [
        ('technologie', 'Technologie'),
        ('finance', 'Finance'),
        ('sante', 'Santé'),
        ('education', 'Éducation'),
        ('commerce', 'Commerce'),
        ('autre', 'Autre'),
    ]

    # =========================
    # INFOS GENERALES
    # =========================
    nom = models.CharField(max_length=200)

    secteur = models.CharField(
        max_length=20,
        choices=SECTEUR_CHOICES
    )

    description = models.TextField(blank=True, null=True)

    # =========================
    # CONTACT
    # =========================
    email_contact = models.EmailField()
    telephone = models.CharField(max_length=20)

    site_web = models.URLField(blank=True, null=True)

    # =========================
    # LOCALISATION
    # =========================
    adresse = models.TextField()
    ville = models.CharField(max_length=100, blank=True, null=True)
    pays = models.CharField(max_length=100, blank=True, null=True)

    # =========================
    # 👑 PROPRIETAIRE
    # =========================
    proprietaire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='organisations'
    )
    """
    👉 Celui qui crée l'organisation
    👉 Peut gérer abonnement et utilisateurs
    """

    # =========================
    # 💳 ABONNEMENT
    # =========================
    abonnement = models.OneToOneField(
        Abonnement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organisation'
    )

    # =========================
    # SYSTEME
    # =========================
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

    # =========================
    # LOGIQUE METIER
    # =========================
    def est_active(self):
        """
        Vérifie si l'organisation est active
        """
        if not self.abonnement:
            return False

        self.abonnement.verifier_expiration()
        return self.abonnement.statut == "actif"

    def nombre_utilisateurs(self):
        """
        Retourne nombre de users dans l'organisation
        """
        return self.utilisateurs.count()

    class Meta:
        ordering = ['-date_creation']