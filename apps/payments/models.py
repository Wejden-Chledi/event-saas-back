# apps/payments/models.py


# Gestion des modèles Django
from django.db import models


# Gestion des dates et heures avec le fuseau horaire Django
from django.utils import timezone


# Génération d'identifiants uniques
import uuid


# Génération de références sécurisées aléatoires
import secrets





# =====================================================
# MODELE : PAIEMENT
# =====================================================
#
# Ce modèle représente une transaction financière
# liée à une inscription à un événement.
#
# Il permet de gérer :
#
# - le montant payé ;
# - la devise ;
# - le moyen de paiement ;
# - le statut de la transaction ;
# - la référence interne ;
# - l'identifiant externe Stripe/PayPal.
#
#
# Flux métier :
#
# Participant
#      |
#      ↓
# Inscription créée
#      |
#      ↓
# Paiement en attente
#      |
#      ↓
# Paiement confirmé
#      |
#      ↓
# Génération du billet QR Code
# =====================================================


class Paiement(models.Model):


    # =================================================
    # STATUTS POSSIBLES D'UN PAIEMENT
    # =================================================
    #
    # en_attente :
    #       paiement créé mais non validé.
    #
    # confirme :
    #       paiement accepté.
    #
    # annule :
    #       paiement annulé.
    #
    # echoue :
    #       problème lors du paiement.
    #
    # rembourse :
    #       montant rendu au participant.
    # =================================================

    STATUT_CHOICES = [

        ('en_attente', 'En attente'),

        ('confirme', 'Confirmé'),

        ('annule', 'Annulé'),

        ('echoue', 'Échoué'),

        ('rembourse', 'Remboursé'),

    ]





    # =================================================
    # MODES DE PAIEMENT DISPONIBLES
    # =================================================

    MODE_CHOICES = [

        ('stripe', 'Stripe'),

        ('paypal', 'PayPal'),

        ('virement', 'Virement'),

        ('autre', 'Autre'),

    ]







    # Identifiant unique du paiement.
    #
    # UUID évite d'exposer des IDs numériques
    # simples dans les URLs API.
    id = models.UUIDField(

        primary_key=True,

        default=uuid.uuid4,

        editable=False

    )





    # Montant de la transaction.
    montant = models.DecimalField(

        max_digits=10,

        decimal_places=2

    )





    # Devise utilisée.
    #
    # Par défaut :
    # Euro.
    devise = models.CharField(

        max_length=10,

        default="EUR"

    )





    # Date automatique de création du paiement.
    date_paiement = models.DateTimeField(

        auto_now_add=True

    )





    # Etat actuel du paiement.
    statut = models.CharField(

        max_length=20,

        choices=STATUT_CHOICES,

        default='en_attente'

    )





    # Moyen de paiement utilisé.
    mode = models.CharField(

        max_length=20,

        choices=MODE_CHOICES,

        default='stripe'

    )







    # =================================================
    # REFERENCES TRANSACTION
    # =================================================


    # Référence interne générée par l'application.
    #
    # Exemple :
    #
    # PAY-A83F92D102
    #
    # Utilisée pour identifier facilement
    # une transaction dans le système.
    reference_transaction = models.CharField(

        max_length=100,

        unique=True,

        null=True,

        blank=True

    )





    # Identifiant fourni par le prestataire externe.
    #
    # Exemple Stripe :
    #
    # pi_123456789
    #
    # Permet de retrouver le paiement
    # chez le fournisseur.
    external_id = models.CharField(

        max_length=255,

        null=True,

        blank=True

    )





    # Description du paiement.
    #
    # Exemple :
    #
    # Inscription événement Tech Conference
    description = models.TextField(

        blank=True,

        null=True

    )







    def __str__(self):

        """
        Affichage lisible d'un paiement
        dans l'administration Django.
        """

        return (
            f"{self.reference_transaction} "
            f"({self.statut}) - "
            f"{self.montant} {self.devise}"
        )








    def save(self, *args, **kwargs):

        """
        Génère automatiquement une référence
        interne avant sauvegarde.
        """


        # Vérifie si la référence existe déjà.
        if not self.reference_transaction:


            # Création d'une référence unique.
            #
            # Exemple :
            # PAY-7FA92B01CD45
            self.reference_transaction = (
                f"PAY-{secrets.token_hex(6).upper()}"
            )



        # Sauvegarde classique Django.
        super().save(
            *args,
            **kwargs
        )








    def confirmer(self, external_id=None):

        """
        Confirme un paiement.

        Cette action déclenche le signal
        post_save qui synchronise :
        
        Paiement → Inscription → Billet
        """


        # Changement du statut
        self.statut = 'confirme'



        # Enregistrement de l'identifiant
        # fourni par Stripe/PayPal.
        if external_id:

            self.external_id = external_id



        # Mise à jour de la date.
        self.date_paiement = timezone.now()



        self.save()








    def annuler(self):

        """
        Annule un paiement.
        """

        self.statut = 'annule'

        self.save()








    def echouer(self):

        """
        Marque le paiement comme échoué.
        """

        self.statut = 'echoue'

        self.save()








    def rembourser(self):

        """
        Marque un paiement comme remboursé.

        Utilisé lorsqu'un participant annule
        une inscription déjà payée.
        """

        self.statut = 'rembourse'

        self.save()