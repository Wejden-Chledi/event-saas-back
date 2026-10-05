# ============================================================================
# Fichier : apps/inscriptions/models.py
#
# Ce fichier contient les modèles liés au processus d'inscription
# des participants aux événements.
#
# Fonctionnalités principales :
#
#   - Gestion des inscriptions aux événements ;
#   - Gestion des statuts d'inscription ;
#   - Association avec les paiements ;
#   - Génération automatique d'une référence paiement ;
#   - Génération automatique des billets avec QR Code ;
#   - Gestion du check-in par le staff ;
#   - Synchronisation automatique paiement -> inscription -> billet.
#
#
# Flux métier :
#
# Participant
#      |
#      ↓
# Inscription
#      |
#      ↓
# Paiement confirmé
#      |
#      ↓
# Statut inscription = payé
#      |
#      ↓
# Génération billet QR Code
#      |
#      ↓
# Scan par Staff (Check-in)
# ============================================================================




# ==============================
# IMPORTATIONS PYTHON
# ==============================


# Génération d'identifiants uniques UUID.
import uuid



# Génération de valeurs aléatoires.
import random



# Gestion des caractères alphanumériques.
import string



# Bibliothèque permettant de générer
# des QR Codes.
import qrcode



# Permet de manipuler des fichiers en mémoire.
from io import BytesIO






# ==============================
# IMPORTATIONS DJANGO
# ==============================


from django.db import models



# Permet de récupérer le modèle utilisateur
# personnalisé configuré dans Django.
from django.contrib.auth import get_user_model



# Permet de créer un fichier Django
# à partir de données en mémoire.
from django.core.files.base import ContentFile



# Signal exécuté après la sauvegarde
# d'un objet Django.
from django.db.models.signals import post_save



# Permet de connecter un signal
# à un modèle précis.
from django.dispatch import receiver





# Import du modèle Paiement.
#
# Permet de synchroniser :
#
# Paiement confirmé
#        ↓
# Inscription payée
#        ↓
# Billet généré
from apps.payments.models import Paiement






# Récupération du modèle utilisateur actif.
Utilisateur = get_user_model()







# ============================================================================
# MODELE : INSCRIPTION
# ============================================================================
#
# Représente l'inscription d'un participant
# à un événement.
#
# Relation :
#
# Participant 1 ---- * Inscription * ---- 1 Evenement
#
# Un participant ne peut pas s'inscrire plusieurs fois
# au même événement.
# ============================================================================


class Inscription(models.Model):


    # ------------------------------------------------------------------------
    # Statuts possibles d'une inscription.
    # ------------------------------------------------------------------------
    #
    # en_attente :
    #       inscription créée mais paiement non confirmé.
    #
    # paye :
    #       paiement validé.
    #
    # utilise :
    #       billet utilisé lors du check-in.
    #
    # annule :
    #       inscription annulée.
    #
    # rembourse :
    #       paiement remboursé.
    # ------------------------------------------------------------------------

    STATUT_CHOICES = [

        ('en_attente', 'En attente'),

        ('paye', 'Payé'),

        ('utilise', 'Utilisé'),

        ('annule', 'Annulé'),

        ('rembourse', 'Remboursé'),

    ]





    # Identifiant unique de l'inscription.
    #
    # UUID est utilisé au lieu d'un entier
    # pour améliorer la sécurité.
    id = models.UUIDField(

        primary_key=True,

        default=uuid.uuid4,

        editable=False

    )





    # Participant inscrit.
    #
    # Un utilisateur peut avoir plusieurs inscriptions.
    participant = models.ForeignKey(

        Utilisateur,

        on_delete=models.CASCADE,

        related_name="inscriptions"

    )





    # Evénement concerné.
    evenement = models.ForeignKey(

        "events.Evenement",

        on_delete=models.CASCADE,

        related_name="inscriptions"

    )





    # Etat actuel de l'inscription.
    statut = models.CharField(

        max_length=20,

        choices=STATUT_CHOICES,

        default="en_attente"

    )





    # Montant réellement payé.
    montant_paye = models.DecimalField(

        max_digits=10,

        decimal_places=2,

        default=0

    )





    # Date automatique de création.
    date_inscription = models.DateTimeField(

        auto_now_add=True

    )





    # Indique si un email de feedback
    # a déjà été envoyé au participant.
    email_feedback_envoye = models.BooleanField(

        default=False

    )





    # Référence unique du paiement.
    #
    # Exemple :
    #
    # EVT-A82K91L02P
    reference_paiement = models.CharField(

        max_length=100,

        unique=True,

        blank=True

    )





    # Relation avec le paiement.
    #
    # Un paiement correspond à une inscription.
    paiement = models.OneToOneField(

        Paiement,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="inscription"

    )





    class Meta:


        # Empêche un participant
        # de s'inscrire plusieurs fois
        # au même événement.
        unique_together = [

            'participant',

            'evenement'

        ]



        # Les inscriptions récentes apparaissent
        # en premier.
        ordering = [

            '-date_inscription'

        ]







    def __str__(self):

        """
        Affichage lisible d'une inscription.
        """

        return (
            f"{self.participant.email} - "
            f"{self.evenement.titre} "
            f"({self.statut})"
        )






    def generer_reference(self):

        """
        Génère une référence paiement unique.

        Format :

            EVT-XXXXXXXXXX
        """



        # Génère uniquement si aucune référence
        # n'existe encore.
        if not self.reference_paiement:


            code = ''.join(

                random.choices(

                    string.ascii_uppercase + string.digits,

                    k=10

                )

            )


            self.reference_paiement = f"EVT-{code}"






    def save(self, *args, **kwargs):


        # Avant chaque sauvegarde :
        # création automatique de la référence.
        self.generer_reference()



        # Sauvegarde normale Django.
        super().save(
            *args,
            **kwargs
        )









# ============================================================================
# MODELE : BILLET
# ============================================================================
#
# Représente le billet électronique envoyé
# au participant après paiement.
#
# Contient :
#
#   - QR Code ;
#   - informations de check-in ;
#   - utilisateur du staff ayant scanné.
# ============================================================================


class Billet(models.Model):


    id = models.UUIDField(

        primary_key=True,

        default=uuid.uuid4,

        editable=False

    )





    # Chaque inscription possède
    # un seul billet.
    inscription = models.OneToOneField(

        Inscription,

        on_delete=models.CASCADE,

        related_name="billet"

    )





    # Image du QR Code généré.
    qr_code = models.ImageField(

        upload_to="billets_qr/",

        blank=True,

        null=True

    )





    # Date de création du billet.
    date_emission = models.DateTimeField(

        auto_now_add=True

    )





    # ------------------------------------------------------------------------
    # CHECK-IN STAFF
    # ------------------------------------------------------------------------


    # Indique si le billet a été utilisé.
    utilise = models.BooleanField(

        default=False

    )



    # Date du scan.
    date_scan = models.DateTimeField(

        null=True,

        blank=True

    )



    # Staff ayant effectué le scan.
    scanne_par = models.ForeignKey(

        Utilisateur,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="billets_scannes"

    )







    def __str__(self):

        return (
            f"Billet {self.id} - "
            f"{self.inscription.evenement.titre}"
        )







    def generer_qr_code(self):

        """
        Génère un QR Code contenant
        l'identifiant du billet.
        """



        # Donnée encodée dans le QR Code.
        qr_data = str(self.id)



        # Création du QR Code.
        qr = qrcode.QRCode(

            version=1,

            box_size=10,

            border=2

        )



        qr.add_data(qr_data)



        qr.make(

            fit=True

        )



        # Création de l'image QR.
        img = qr.make_image(

            fill_color="black",

            back_color="white"

        )



        # Sauvegarde temporaire en mémoire.
        buffer = BytesIO()



        img.save(

            buffer,

            format="PNG"

        )





        # Nom du fichier enregistré.
        filename = f"billet_{self.id}.png"





        # Ajout du fichier au champ ImageField.
        #
        # save=False évite une boucle infinie
        # car on est déjà dans save().
        self.qr_code.save(

            filename,

            ContentFile(buffer.getvalue()),

            save=False

        )







    def save(self, *args, **kwargs):


        # Génère le QR uniquement :
        #
        # - si paiement effectué ;
        # - si aucun QR existant.
        if (

            self.inscription.statut in [

                'paye',

                'utilise'

            ]

            and not self.qr_code

        ):


            self.generer_qr_code()





        super().save(

            *args,

            **kwargs

        )









# ============================================================================
# SIGNAL : SYNCHRONISATION PAIEMENT / INSCRIPTION
# ============================================================================
#
# Ce signal est exécuté automatiquement
# après chaque modification d'un paiement.
#
# Objectif :
#
# Paiement confirmé
#       ↓
# Mise à jour inscription
#       ↓
# Création billet QR Code
# ============================================================================


@receiver(
    post_save,
    sender=Paiement
)

def synchroniser_paiement_et_inscription(
    sender,
    instance,
    created,
    **kwargs
):


    """
    Synchronise automatiquement
    le paiement avec l'inscription.
    """



    try:


        # Vérifie si le paiement possède
        # une inscription associée.
        if hasattr(instance, 'inscription'):


            inscription = instance.inscription






            # ---------------------------------------------------------------
            # Paiement confirmé
            # ---------------------------------------------------------------


            if instance.statut == "confirme":


                # Mise à jour du statut.
                inscription.statut = "paye"



                # Enregistrement du montant payé.
                inscription.montant_paye = instance.montant



                inscription.save()



                # Création automatique du billet.
                #
                # Le QR Code sera généré
                # automatiquement dans Billet.save().
                Billet.objects.get_or_create(

                    inscription=inscription

                )






            # ---------------------------------------------------------------
            # Paiement remboursé
            # ---------------------------------------------------------------


            elif instance.statut == "rembourse":


                inscription.statut = "rembourse"



                inscription.save()



                # Suppression du billet
                # après remboursement.
                if hasattr(inscription, 'billet'):

                    inscription.billet.delete()







    except Exception as e:


        # En production :
        #
        # utiliser logger.error()
        # au lieu de print().
        print(
            f"Erreur Signal Paiement/Inscription: {e}"
        )