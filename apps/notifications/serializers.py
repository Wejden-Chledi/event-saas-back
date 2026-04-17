# apps/notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    # Champs additionnels pour faciliter l'affichage côté Frontend
    destinataire_email = serializers.EmailField(source="destinataire.email", read_only=True)
    destinataire_nom = serializers.CharField(source="destinataire.nom", read_only=True)
    destinataire_prenom = serializers.CharField(source="destinataire.prenom", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", 
            "destinataire", 
            "destinataire_email", 
            "destinataire_nom", 
            "destinataire_prenom",
            "type_notification", 
            "sujet", 
            "message", 
            "html_message",
            "date_creation", 
            "date_envoi", 
            "statut"
        ]
        # On protège les champs techniques pour qu'ils ne soient pas modifiables via l'API
        read_only_fields = ["date_creation", "date_envoi", "statut"]

    def validate_type_notification(self, value):
        """Exemple de validation : s'assurer que le type est supporté."""
        choices = dict(Notification.TYPE_CHOICES)
        if value not in choices:
            raise serializers.ValidationError(f"Type de notification '{value}' non supporté.")
        return value