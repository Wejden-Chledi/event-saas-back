from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


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

        return self.create_user(email, nom, prenom, password, **extra_fields)



class Utilisateur(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ("proprietaire", "Proprietaire"),
        ("gestionnaire", "Gestionnaire"),
        ("staff", "Staff"),
        ("participant", "Participant"),
    ]

    STATUT_CHOICES = [
        ("actif", "Actif"),
        ("suspendu", "Suspendu"),
    ]

    email = models.EmailField(unique=True)

    nom = models.CharField(max_length=100)

    prenom = models.CharField(max_length=100)

    telephone = models.CharField(max_length=15, blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="participant"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="actif"
    )

    date_inscription = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.email})"

    def modifierProfil(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()



class ParticipantProfile(models.Model):

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="participant_profile"
    )

    date_naissance = models.DateField(null=True, blank=True)

    adresse = models.TextField(blank=True)

    ville = models.CharField(max_length=100, blank=True)

    code_postal = models.CharField(max_length=10, blank=True)

    profession = models.CharField(max_length=100, blank=True)

    bio = models.TextField(blank=True)

    preferences_evenements = models.JSONField(default=list, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil de {self.utilisateur.nom} {self.utilisateur.prenom}"

    def get_age(self):

        if self.date_naissance:

            today = timezone.now().date()

            return (
                today.year
                - self.date_naissance.year
                - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
            )

        return None