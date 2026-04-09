# apps/feedback/models.py
from django.db import models
from django.contrib.auth import get_user_model
from apps.events.models import Evenement
from apps.organisations.models import Organisation

Utilisateur = get_user_model()

class Feedback(models.Model):
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name="feedbacks")
    participant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="avis_donnes")
    
    # Notes (1 à 5)
    note_globale = models.PositiveSmallIntegerField()
    organisation = models.PositiveSmallIntegerField()
    contenu = models.PositiveSmallIntegerField()
    intervenants = models.PositiveSmallIntegerField()
    lieu = models.PositiveSmallIntegerField()
    ambiance = models.PositiveSmallIntegerField()
    rapport_qualite_prix = models.PositiveSmallIntegerField()

    commentaire = models.TextField(blank=True)
    recommande = models.BooleanField(default=True)
    
    # IA - Sentiment individuel (Positif, Neutre, Négatif)
    sentiment_ia = models.CharField(max_length=50, blank=True, null=True) 
    
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('evenement', 'participant')

class RapportIAEvenement(models.Model):
    evenement = models.OneToOneField(Evenement, on_delete=models.CASCADE, related_name="analyse_feedback")
    resume_ia = models.TextField() # Analyse intelligente
    aide_decision = models.TextField(blank=True, null=True) # Actions concrètes
    date_generation = models.DateTimeField(auto_now=True)

class RapportGlobalOrganisation(models.Model):
    organisation = models.OneToOneField(
        Organisation, 
        on_delete=models.CASCADE, 
        related_name="rapport_ia_global"
    )
    analyse_strategique = models.TextField()
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)