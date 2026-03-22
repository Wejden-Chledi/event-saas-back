# apps/payments/serializers.py
from rest_framework import serializers
from .models import Paiement

class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = [
            "id",
            "montant",
            "devise",
            "date_paiement",
            "statut",
            "mode",
            "reference_transaction",
            "description",
        ]
        read_only_fields = [
            "id",
            "statut",           
            "date_paiement",   
            "reference_transaction",
        ]

# Serializer pour confirmer le paiement
class PaiementConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = ["id"]