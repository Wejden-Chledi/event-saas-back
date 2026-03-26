from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    destinataire_email = serializers.EmailField(source="destinataire.email", read_only=True)
    destinataire_nom = serializers.CharField(source="destinataire.nom", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", "destinataire", "destinataire_email", "destinataire_nom",
            "type_notification", "sujet", "message", 
            "date_creation", "date_envoi", "statut"
        ]
        read_only_fields = ["date_creation", "date_envoi", "statut"]