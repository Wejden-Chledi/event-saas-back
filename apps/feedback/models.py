# apps/feedback/models.py

from django.db import models
from django.contrib.auth import get_user_model
from apps.events.models import Evenement
from apps.organisations.models import Organisation

Utilisateur = get_user_model()


class Feedback(models.Model):
    """
    Modèle représentant l'avis d'un participant après un événement.
    Chaque participant peut donner un seul feedback par événement.
    """

    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    participant = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="avis_donnes"
    )

    # Évaluation détaillée de l'événement sur une échelle de 1 à 5
    note_globale = models.PositiveSmallIntegerField()
    organisation = models.PositiveSmallIntegerField()
    contenu = models.PositiveSmallIntegerField()
    intervenants = models.PositiveSmallIntegerField()
    lieu = models.PositiveSmallIntegerField()
    ambiance = models.PositiveSmallIntegerField()
    rapport_qualite_prix = models.PositiveSmallIntegerField()

    # Commentaire libre laissé par le participant
    commentaire = models.TextField(blank=True)

    # Indique si le participant recommande l'événement
    recommande = models.BooleanField(default=True)

    # Résultat de l'analyse automatique du sentiment par l'IA
    # Valeurs possibles : Positif, Neutre, Négatif
    sentiment_ia = models.CharField(max_length=50, blank=True, null=True)

    # Date de création automatique du feedback
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Empêche un participant de donner plusieurs avis pour le même événement
        unique_together = ('evenement', 'participant')


class RapportIAEvenement(models.Model):
    """
    Rapport généré par l'intelligence artificielle
    pour analyser les retours d'un événement.
    """

    # Un événement possède un seul rapport IA
    evenement = models.OneToOneField(
        Evenement,
        on_delete=models.CASCADE,
        related_name="analyse_feedback"
    )

    # Résumé automatique des avis collectés
    resume_ia = models.TextField()

    # Suggestions et actions recommandées par l'IA
    aide_decision = models.TextField(blank=True, null=True)

    # Date de dernière génération ou mise à jour du rapport
    date_generation = models.DateTimeField(auto_now=True)


class RapportGlobalOrganisation(models.Model):
    """
    Rapport stratégique global généré pour une organisation.
    Il regroupe les analyses des différents événements.
    """

    # Relation unique entre une organisation et son rapport IA global
    organisation = models.OneToOneField(
        Organisation,
        on_delete=models.CASCADE,
        related_name="rapport_ia_global"
    )

    # Analyse stratégique générée par l'IA
    analyse_strategique = models.TextField()

    # Date de dernière actualisation du rapport
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)