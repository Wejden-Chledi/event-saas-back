# apps/organisations/models.py
from django.db import models
from django.utils import timezone
from apps.users.models import Utilisateur


class Abonnement(models.Model):
    TYPE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
    ]
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('expiré', 'Expiré'),
        ('en_attente', 'En attente'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='mensuel')
    dateDebut = models.DateField(verbose_name="Date de début")
    dateFin = models.DateField(verbose_name="Date de fin")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    dateCreation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    def renouveler(self, mois=1):
        from datetime import timedelta
        self.dateFin += timedelta(days=30 * mois)
        self.statut = 'actif'
        self.save()

    def suspendre(self):
        self.statut = 'suspendu'
        self.save()

    def verifier_expiration(self):
        if timezone.now().date() > self.dateFin and self.statut == 'actif':
            self.statut = 'expiré'
            self.save()

    def __str__(self):
        return f"Abonnement {self.type} - {self.statut}"


class Organisation(models.Model):
    SECTEUR_CHOICES = [
        ('technologie', 'Technologie'),
        ('finance', 'Finance'),
        ('sante', 'Santé'),
        ('education', 'Éducation'),
        ('commerce', 'Commerce'),
        ('autre', 'Autre'),
    ]
    
    STATUT_ABONNEMENT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('essai', 'Essai gratuit'),
        ('suspendu', 'Suspendu'),
    ]

    nom = models.CharField(max_length=200, verbose_name="Nom de l'organisation")
    secteur = models.CharField(max_length=20, choices=SECTEUR_CHOICES, verbose_name="Secteur d'activité")
    logo = models.TextField(blank=True, null=True, verbose_name="Logo (URL ou base64)")
    dateCreation = models.DateField(default=timezone.now, verbose_name="Date de création")
    statutAbonnement = models.CharField(
        max_length=20, 
        choices=STATUT_ABONNEMENT_CHOICES, 
        default='essai',
        verbose_name="Statut de l'abonnement"
    )
    emailContact = models.EmailField(verbose_name="Email de contact")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    adresse = models.TextField(verbose_name="Adresse")
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")  # ← ajouté
    pays = models.CharField(max_length=100, blank=True, null=True, verbose_name="Pays")     # ← ajouté
    siteWeb = models.URLField(blank=True, null=True, verbose_name="Site web")
    
    # Relations
    proprietaire = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name='organisations',
        verbose_name="Propriétaire"
    )
    abonnement = models.OneToOneField(
        Abonnement, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='organisation',
        verbose_name="Abonnement"
    )

    def GererOrganisation(self):
        if self.abonnement:
            self.abonnement.verifier_expiration()
            self.statutAbonnement = self.abonnement.statut
        else:
            self.statutAbonnement = 'inactif'
        self.save()

    def __str__(self):
        return f"{self.nom} ({self.secteur})"

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        ordering = ['-dateCreation']