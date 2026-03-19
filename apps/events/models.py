# apps/events/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

Utilisateur = get_user_model()

class Evenement(models.Model):
    """
    Modèle représentant un événement créé par un gestionnaire.
    Chaque événement est lié à une organisation et à son créateur (gestionnaire).
    """

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('publie', 'Publié'),
        ('annule', 'Annulé'),
        ('termine', 'Terminé'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField()
    lieu = models.CharField(max_length=200)

    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField(default=timezone.now)

    capacite_max = models.PositiveIntegerField()
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="evenements"
    )

    createur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="evenements_crees"
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_debut']

    def __str__(self):
        return self.titre

    # ======== Méthodes utilitaires ========

    def places_disponibles(self):
        """Retourne le nombre de places encore disponibles (inscriptions payées)."""
        total = self.inscriptions.filter(statut="paye").count()
        return max(0, self.capacite_max - total)

    def est_complet(self):
        """Vérifie si l'événement est complet."""
        return self.places_disponibles() <= 0

    def publier(self):
        """Publie l'événement."""
        self.statut = "publie"
        self.save()

    def annuler(self):
        """Annule l'événement."""
        self.statut = "annule"
        self.save()


class AssignationEvenement(models.Model):
    """
    Assignation d'un staff à un événement spécifique.
    Permet de gérer qui doit être présent le jour J.
    """

    staff = models.ForeignKey(
        "users.Utilisateur",
        limit_choices_to={'role': 'staff'},  # seulement les staff peuvent être assignés
        on_delete=models.CASCADE,
        related_name="assignations"
    )

    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name="staff_assignes"
    )

    date_assignation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['staff', 'evenement']

    def __str__(self):
        return f"{self.staff} -> {self.evenement}"
    


class EventPhoto(models.Model):
    """
    Modèle pour stocker les photos d'un événement.
    Chaque photo est liée à un événement spécifique.
    Utile pour afficher des galeries ou des médias associés à l'événement.
    """

    evenement = models.ForeignKey(
        "Evenement",
        on_delete=models.CASCADE,
        related_name="photos"
    )

    # Stocke l'image uploadée (le fichier sera enregistré dans media/events/)
    image = models.ImageField(upload_to="events/")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo de l'événement: {self.evenement.titre} ({self.id})"