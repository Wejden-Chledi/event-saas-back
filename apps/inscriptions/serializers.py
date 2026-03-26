# apps/inscriptions/serializers.py
from rest_framework import serializers
from .models import Inscription, Billet
from apps.payments.models import Paiement
from django.db import transaction

class InscriptionSerializer(serializers.ModelSerializer):
    participant_nom = serializers.CharField(source="participant.nom", read_only=True)
    participant_prenom = serializers.CharField(source="participant.prenom", read_only=True)
    evenement_titre = serializers.CharField(source="evenement.titre", read_only=True)
    evenement_prix = serializers.DecimalField(source="evenement.prix", max_digits=10, decimal_places=2, read_only=True)
    statut_label = serializers.CharField(source="get_statut_display", read_only=True)
    statut_paiement = serializers.CharField(source="paiement.statut", read_only=True)

    class Meta:
        model = Inscription
        fields = [
            "id", "participant", "evenement", "date_inscription", "statut", "statut_label",
            "statut_paiement", "montant_paye", "reference_paiement", "paiement",
            "participant_nom", "participant_prenom", "evenement_titre", "evenement_prix",
        ]
        read_only_fields = ["date_inscription", "reference_paiement", "montant_paye", "statut"]

class InscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscription
        fields = ["evenement"]

    def validate(self, data):
        user = self.context["request"].user
        evenement = data["evenement"]

        # 1. Vérifier si l'utilisateur est déjà inscrit
        if Inscription.objects.filter(participant=user, evenement=evenement).exists():
            raise serializers.ValidationError("Vous êtes déjà inscrit à cet événement.")

        # 2. Vérifier si l'événement est complet
        if evenement.est_complet():
            raise serializers.ValidationError("Désolé, cet événement est déjà complet.")

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        evenement = validated_data["evenement"]

        with transaction.atomic():
            # Création du paiement en attente
            paiement = Paiement.objects.create(
                montant=evenement.prix,
                statut='en_attente',
                mode='stripe',
                description=f"Inscription : {evenement.titre} - {user.email}"
            )

            # Création de l'inscription liée
            inscription = Inscription.objects.create(
                participant=user,
                evenement=evenement,
                montant_paye=0,
                paiement=paiement,
                statut='en_attente'
            )
            
        return inscription

class BilletSerializer(serializers.ModelSerializer):
    evenement_titre = serializers.CharField(source="inscription.evenement.titre", read_only=True)
    date_evenement = serializers.DateTimeField(source="inscription.evenement.date_debut", read_only=True)
    lieu = serializers.CharField(source="inscription.evenement.lieu", read_only=True)
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Billet
        fields = [
            "id", "inscription", "qr_code_url", "date_emission", 
            "utilise", "evenement_titre", "date_evenement", "lieu"
        ]

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return self.context['request'].build_absolute_uri(obj.qr_code.url)
        return None