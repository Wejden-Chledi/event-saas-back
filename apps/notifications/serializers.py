# apps/notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    destinataire_email = serializers.CharField(source="destinataire.email", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "destinataire",
            "destinataire_email",
            "type_notification",
            "sujet",
            "message",
            "date_creation",
            "date_envoi",
            "statut",
        ]
        read_only_fields = [
            "date_creation",
            "date_envoi",
            "statut",
            "destinataire_email",
        ]