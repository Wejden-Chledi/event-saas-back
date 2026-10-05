# ============================================================================
# Fichier : apps/organisations/models.py
#
# Ce fichier contient les modèles liés à la gestion des organisations
# dans la plateforme SaaS.
#
# Il définit principalement :
#
#   - Le modèle Abonnement :
#       Gestion des plans d'abonnement et de leur état.
#
#   - Le modèle Organisation :
#       Entité principale du système SaaS représentant
#       une entreprise cliente de la plateforme.
#
# Chaque organisation possède :
#       - un propriétaire ;
#       - un abonnement ;
#       - des informations générales ;
#       - des informations de contact ;
#       - une localisation.
# ============================================================================


# ==============================
# IMPORTATION DES MODULES DJANGO
# ==============================

# Module Django permettant de créer des modèles
# et de définir les champs de la base de données.
from django.db import models

# Fournit des fonctions liées aux dates et heures
# compatibles avec le système de fuseau horaire Django.
from django.utils import timezone


# Importation du modèle utilisateur personnalisé.
# Il est utilisé pour définir la relation entre
# une organisation et son propriétaire.
from apps.users.models import Utilisateur



# ============================================================================
# MODELE : ABONNEMENT
# ============================================================================
#
# Ce modèle représente l'abonnement souscrit
# par une organisation.
#
# Il permet de gérer :
#   - le type de plan ;
#   - la période de validité ;
#   - le statut ;
#   - le montant payé.
# ============================================================================

class Abonnement(models.Model):


    # ------------------------------------------------------------------------
    # Plans d'abonnement disponibles.
    #
    # Chaque valeur contient :
    #   - la valeur stockée en base ;
    #   - le texte affiché dans l'interface.
    # ------------------------------------------------------------------------
    PLAN_CHOICES = [
        ('gratuit', 'Gratuit'),
        ('basique', 'Basique'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    ]


    # ------------------------------------------------------------------------
    # Etats possibles d'un abonnement.
    # ------------------------------------------------------------------------
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('expire', 'Expiré'),
    ]


    # Type de formule choisie par l'organisation.
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='gratuit'
    )


    # Date de début de l'abonnement.
    #
    # timezone.localdate permet d'enregistrer uniquement
    # la date actuelle sans l'heure.
    date_debut = models.DateField(
        default=timezone.localdate
    )


    # Date de fin de l'abonnement.
    #
    # Peut être vide pour les abonnements gratuits
    # ou sans expiration définie.
    date_fin = models.DateField(
        null=True,
        blank=True
    )


    # Etat actuel de l'abonnement.
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='actif'
    )


    # Montant payé pour l'abonnement.
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )


    # Date automatique de création.
    #
    # auto_now_add ajoute automatiquement
    # la date lors de la création de l'objet.
    date_creation = models.DateTimeField(
        auto_now_add=True
    )


    # Représentation texte de l'objet.
    def __str__(self):
        return f"{self.plan} - {self.statut}"


    # ------------------------------------------------------------------------
    # Vérification de l'expiration.
    #
    # Cette méthode compare la date actuelle
    # avec la date de fin de l'abonnement.
    #
    # Si l'abonnement est dépassé,
    # son statut devient "expire".
    # ------------------------------------------------------------------------
    def verifier_expiration(self):

        if self.date_fin and timezone.now().date() > self.date_fin:

            self.statut = 'expire'

            self.save()



# ============================================================================
# MODELE : ORGANISATION
# ============================================================================
#
# Modèle principal du système SaaS.
#
# Une organisation représente un client utilisant
# la plateforme de gestion d'événements.
#
# Elle possède :
#   - un propriétaire ;
#   - un abonnement ;
#   - des utilisateurs ;
#   - des informations administratives.
# ============================================================================


class Organisation(models.Model):


    # ------------------------------------------------------------------------
    # Secteurs d'activité possibles.
    # ------------------------------------------------------------------------
    SECTEUR_CHOICES = [
        ('technologie', 'Technologie'),
        ('finance', 'Finance'),
        ('sante', 'Santé'),
        ('education', 'Éducation'),
        ('commerce', 'Commerce'),
        ('autre', 'Autre'),
    ]



    # =========================
    # INFORMATIONS GENERALES
    # =========================


    # Nom de l'organisation.
    nom = models.CharField(
        max_length=200
    )


    # Domaine d'activité.
    secteur = models.CharField(
        max_length=20,
        choices=SECTEUR_CHOICES
    )


    # Description facultative.
    description = models.TextField(
        blank=True,
        null=True
    )



    # =========================
    # INFORMATIONS DE CONTACT
    # =========================


    # Adresse email principale.
    email_contact = models.EmailField()


    # Numéro de téléphone.
    telephone = models.CharField(
        max_length=20
    )


    # Site web optionnel.
    site_web = models.URLField(
        blank=True,
        null=True
    )



    # =========================
    # LOCALISATION
    # =========================


    # Adresse complète.
    adresse = models.TextField()


    # Ville de l'organisation.
    ville = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    # Pays de l'organisation.
    pays = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )



    # =========================
    # PROPRIETAIRE
    # =========================


    # Relation avec l'utilisateur propriétaire.
    #
    # Une organisation appartient à un propriétaire.
    #
    # on_delete=models.CASCADE signifie que si
    # le propriétaire est supprimé,
    # l'organisation sera également supprimée.
    #
    # related_name permet d'accéder aux organisations
    # d'un utilisateur :
    #
    # utilisateur.organisations.all()
    proprietaire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='organisations'
    )



    # =========================
    # ABONNEMENT
    # =========================


    # Relation OneToOne avec l'abonnement.
    #
    # Une organisation possède au maximum
    # un seul abonnement.
    #
    # SET_NULL conserve l'organisation même si
    # l'abonnement est supprimé.
    abonnement = models.OneToOneField(
        Abonnement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organisation'
    )



    # =========================
    # INFORMATIONS SYSTEME
    # =========================


    # Date automatique de création.
    date_creation = models.DateTimeField(
        auto_now_add=True
    )


    # Permet d'activer ou désactiver une organisation.
    actif = models.BooleanField(
        default=True
    )



    # Affichage du nom de l'organisation.
    def __str__(self):

        return self.nom



    # =========================================================================
    # LOGIQUE METIER
    # =========================================================================


    # Vérifie si l'organisation peut utiliser la plateforme.
    #
    # Une organisation est active uniquement si :
    #   - elle possède un abonnement ;
    #   - son abonnement n'est pas expiré.
    def est_active(self):

        if not self.abonnement:

            return False


        self.abonnement.verifier_expiration()


        return self.abonnement.statut == "actif"



    # Retourne le nombre d'utilisateurs
    # appartenant à cette organisation.
    def nombre_utilisateurs(self):

        """
        Safe version :
        évite une erreur si la relation utilisateurs
        n'existe pas.
        """

        if hasattr(self, "utilisateurs"):

            return self.utilisateurs.count()


        return 0



    # Configuration supplémentaire du modèle.
    class Meta:

        # Les organisations seront affichées
        # de la plus récente à la plus ancienne.
        ordering = ['-date_creation']