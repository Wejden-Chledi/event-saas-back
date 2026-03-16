# src/apps/proprietaire/models.py

from django.db import models
from django.utils import timezone
from apps.users.models import Utilisateur
from apps.organisations.models import Organisation


class InformationOrganisation(models.Model):
    organisation = models.OneToOneField(
        Organisation,
        on_delete=models.CASCADE,
        related_name='informations'
    )

    siret = models.CharField(max_length=14, blank=True, null=True)
    rcs = models.CharField(max_length=10, blank=True, null=True)
    forme_juridique = models.CharField(max_length=50, blank=True, null=True)

    capital_social = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    iban = models.CharField(max_length=34, blank=True, null=True)
    bic = models.CharField(max_length=11, blank=True, null=True)

    nombre_employes = models.IntegerField(blank=True, null=True)
    chiffre_affaires = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    annee_creation = models.IntegerField(blank=True, null=True)

    linkedin = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    mission = models.TextField(blank=True, null=True)

    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Informations - {self.organisation.nom}"


class Gestionnaire(models.Model):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name='gestionnaires'
    )

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='gestionnaire_profile',
        null=True,
        blank=True
    )

    departement = models.CharField(max_length=100, blank=True, null=True)

    peut_gerer_evenements = models.BooleanField(default=True)
    peut_gerer_finances = models.BooleanField(default=False)
    peut_gerer_personnel = models.BooleanField(default=False)
    peut_voir_rapports = models.BooleanField(default=True)

    actif = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.utilisateur:
            return f"{self.utilisateur.nom} {self.utilisateur.prenom} - {self.organisation.nom}"
        return f"Gestionnaire - {self.organisation.nom}"

    class Meta:
        ordering = ['utilisateur__nom', 'utilisateur__prenom']


class DemandeAbonnement(models.Model):

    TYPE_CHOICES = [
        ('gratuit', 'Gratuit'),
        ('basique', 'Basique'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('refuse', 'Refusé'),
    ]

    MONTANTS = {
        'gratuit': 0,
        'basique': 50.0,
        'pro': 140.0,
        'premium': 500.0,
    }

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name='demandes_abonnement'
    )

    type_demande = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant_propose = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    raison = models.TextField(blank=True, null=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    date_demande = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(blank=True, null=True)
    commentaire_admin = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calcul automatique du montant si non fourni
        if not self.montant_propose:
            self.montant_propose = self.MONTANTS.get(self.type_demande, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Demande {self.type_demande.capitalize()} - {self.organisation.nom}"

    def approuver(self, commentaire=''):
        self.statut = 'approuve'
        self.commentaire_admin = commentaire
        self.date_traitement = timezone.now()
        self.save()

    def refuser(self, commentaire=''):
        self.statut = 'refuse'
        self.commentaire_admin = commentaire
        self.date_traitement = timezone.now()
        self.save()