# apps/users/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# =====================================================
# MANAGER PERSONNALISÉ
# =====================================================
class UserManager(BaseUserManager):
    def create_user(self, email, nom, prenom, password=None, role="participant", **extra_fields):
        if not email:
            raise ValueError("L'email doit être fourni")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nom=nom,
            prenom=prenom,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, prenom, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "proprietaire")
        # Le superuser est toujours actif
        extra_fields.setdefault("statut", "actif")
        return self.create_user(email, nom, prenom, password, **extra_fields)


# =====================================================
# MODELE UTILISATEUR CENTRAL
# =====================================================
class Utilisateur(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("proprietaire", "Propriétaire"),
        ("gestionnaire", "Gestionnaire"),
        ("staff", "Staff"),
        ("participant", "Participant"),
    ]

    STATUT_CHOICES = [
        ("actif", "Actif"),
        ("inactif", "Inactif"),
    ]
    createur = models.ForeignKey(
            'self',
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name="utilisateurs_crees"
        )
    # =========================
    # INFOS PERSONNELLES
    # =========================
    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=15, blank=True, null=True)
    date_naissance = models.DateField(null=True, blank=True)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, blank=True)

    # =========================
    # ORGANISATION
    # =========================
    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="utilisateurs"
    )

    # =========================
    # ROLE + STATUT
    # =========================
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="participant")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="actif")

    # =========================
    # SYSTEME
    # =========================
    date_inscription = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)  # uniquement pour accès admin Django

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.email})"

    # =========================
    # MÉTHODE UTILE
    # =========================
    def modifierProfil(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()