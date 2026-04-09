# apps/feedback/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from apps.events.models import Evenement

Utilisateur = get_user_model()

class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name="feedbacks")
    participant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="avis_donnes")
    
    
        # Évaluations avec validateurs
        # ⭐ Notes détaillées (1 à 5)
    note_globale = models.PositiveSmallIntegerField()

    organisation = models.PositiveSmallIntegerField()   # organisation générale
    contenu = models.PositiveSmallIntegerField()        # qualité du contenu
    intervenants = models.PositiveSmallIntegerField()   # qualité des speakers
    lieu = models.PositiveSmallIntegerField()           # lieu & logistique
    ambiance = models.PositiveSmallIntegerField()       # ambiance générale
    rapport_qualite_prix = models.PositiveSmallIntegerField()  # value for money

    # 💬 commentaire
    commentaire = models.TextField(blank=True)

    # 👍 recommandation
    recommande = models.BooleanField(default=True)
    
    # IA - Analyse individuelle
    sentiment_ia = models.CharField(max_length=50, blank=True) 
    
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('evenement', 'participant')

class RapportIAEvenement(models.Model):
    evenement = models.OneToOneField(Evenement, on_delete=models.CASCADE, related_name="analyse_feedback")
    resume_ia = models.TextField()
    points_amelioration = models.TextField(blank=True, null=True)
    date_generation = models.DateTimeField(auto_now=True)