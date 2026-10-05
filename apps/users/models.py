# Fichier : apps/users/models.py
#
# Ce fichier contient les modèles liés à la gestion des utilisateurs
# de la plateforme Eventora.
#
# Il définit :
#
#   - UserManager :
#       Gestionnaire personnalisé permettant la création des utilisateurs
#       standards et des administrateurs.
#
#   - Utilisateur :
#       Modèle utilisateur principal de l'application.
#       Il remplace le modèle utilisateur Django par défaut et permet
#       de gérer les rôles, les statuts et les relations avec les
#       organisations.
#
# Ce modèle permet de gérer l'authentification, les permissions et
# la gestion des différents profils utilisateurs :
# propriétaire, gestionnaire, staff et participant.



from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone



# ============================================================================
# MANAGER UTILISATEUR PERSONNALISÉ
#
# Ce manager centralise la logique de création des utilisateurs.
# Il permet notamment de :
#   - Créer des comptes utilisateurs classiques.
#   - Créer des comptes administrateurs avec des privilèges élevés.
# ============================================================================

class UserManager(BaseUserManager):

    # ------------------------------------------------------------------------
    # Création d'un utilisateur standard
    # ------------------------------------------------------------------------

    def create_user(self, email, nom, prenom, password=None, role="participant", **extra_fields):

        # Vérification obligatoire de l'adresse email
        if not email:
            raise ValueError("L'email doit être fourni")


        # Normalisation de l'email pour éviter les doublons liés à la casse
        email = self.normalize_email(email)


        # Création de l'objet utilisateur
        user = self.model(
            email=email,
            nom=nom,
            prenom=prenom,
            role=role,
            **extra_fields
        )


        # Chiffrement du mot de passe avant sauvegarde
        user.set_password(password)


        # Enregistrement dans la base de données
        user.save(using=self._db)

        return user



    # ------------------------------------------------------------------------
    # Création d'un administrateur Django (superuser)
    # ------------------------------------------------------------------------

    def create_superuser(self, email, nom, prenom, password=None, **extra_fields):

        # Attribution automatique des permissions administrateur
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # Un superuser correspond au rôle propriétaire
        extra_fields.setdefault("role", "proprietaire")
        extra_fields.setdefault("statut", "actif")


        return self.create_user(
            email,
            nom,
            prenom,
            password,
            **extra_fields
        )



# ============================================================================
# MODELE UTILISATEUR CENTRAL
#
# Hérite de :
#
#   - AbstractBaseUser :
#       Fournit la gestion de l'authentification et des mots de passe.
#
#   - PermissionsMixin :
#       Ajoute le système de permissions Django.
#
# Ce modèle remplace le modèle User Django par défaut.
# ============================================================================

class Utilisateur(AbstractBaseUser, PermissionsMixin):


    # ------------------------------------------------------------------------
    # Gestion des rôles utilisateurs
    # ------------------------------------------------------------------------

    ROLE_CHOICES = [
        ("proprietaire", "Propriétaire"),
        ("gestionnaire", "Gestionnaire"),
        ("staff", "Staff"),
        ("participant", "Participant"),
    ]


    # Gestion du statut du compte
    STATUT_CHOICES = [
        ("actif", "Actif"),
        ("inactif", "Inactif"),
    ]



    # ------------------------------------------------------------------------
    # Relation hiérarchique entre utilisateurs
    #
    # Permet d'identifier l'utilisateur ayant créé un autre utilisateur.
    # Exemple :
    # Un propriétaire peut créer un gestionnaire ou un membre staff.
    # ------------------------------------------------------------------------

    createur = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="utilisateurs_crees"
    )



    # ------------------------------------------------------------------------
    # Informations personnelles
    # ------------------------------------------------------------------------

    email = models.EmailField(unique=True)

    nom = models.CharField(max_length=100)

    prenom = models.CharField(max_length=100)

    telephone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    date_naissance = models.DateField(
        null=True,
        blank=True
    )

    adresse = models.TextField(blank=True)

    ville = models.CharField(
        max_length=100,
        blank=True
    )

    pays = models.CharField(
        max_length=100,
        blank=True
    )



    # ------------------------------------------------------------------------
    # Organisation associée
    #
    # Un utilisateur peut appartenir à une organisation.
    # Cette relation permet de gérer les accès selon l'organisation.
    # ------------------------------------------------------------------------

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="utilisateurs"
    )



    # ------------------------------------------------------------------------
    # Gestion du rôle et du statut
    # ------------------------------------------------------------------------

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



    # ------------------------------------------------------------------------
    # Informations système
    # ------------------------------------------------------------------------

    date_inscription = models.DateTimeField(
        default=timezone.now
    )


    # Autorise l'accès à l'administration Django
    is_staff = models.BooleanField(
        default=False
    )



    # Association avec le manager personnalisé
    objects = UserManager()



    # Configuration de l'authentification Django
    # L'utilisateur se connecte avec son email
    USERNAME_FIELD = "email"


    # Champs obligatoires lors de la création via createsuperuser
    REQUIRED_FIELDS = [
        "nom",
        "prenom"
    ]



    # ------------------------------------------------------------------------
    # Représentation textuelle de l'utilisateur
    # ------------------------------------------------------------------------

    def __str__(self):

        return f"{self.nom} {self.prenom} ({self.email})"



    # ------------------------------------------------------------------------
    # Modification dynamique du profil utilisateur
    #
    # Permet de modifier plusieurs attributs sans créer plusieurs méthodes.
    #
    # ------------------------------------------------------------------------

    def modifierProfil(self, **kwargs):

        for key, value in kwargs.items():

            setattr(
                self,
                key,
                value
            )

        self.save()