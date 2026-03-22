# apps/inscriptions/serializers.py
from rest_framework import serializers
from .models import Inscription, Billet
from apps.payments.models import Paiement

# ================================
# INSCRIPTION (Lecture)
# ================================
class InscriptionSerializer(serializers.ModelSerializer):
    participant_nom = serializers.CharField(source="participant.nom", read_only=True)
    participant_prenom = serializers.CharField(source="participant.prenom", read_only=True)
    evenement_titre = serializers.CharField(source="evenement.titre", read_only=True)
    evenement_prix = serializers.DecimalField(source="evenement.prix", max_digits=10, decimal_places=2, read_only=True)
    statut_paiement = serializers.CharField(source="paiement.statut", read_only=True)

    class Meta:
        model = Inscription
        fields = [
            "id",
            "participant",
            "evenement",
            "date_inscription",
            "statut_paiement",
            "montant_paye",
            "reference_paiement",
            "paiement",
            "participant_nom",
            "participant_prenom",
            "evenement_titre",
            "evenement_prix",
        ]
        read_only_fields = ["date_inscription", "reference_paiement", "montant_paye"]

# ================================
# INSCRIPTION CREATE
# ================================
class InscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscription
        fields = ["evenement"]

    def create(self, validated_data):
        user = self.context["request"].user
        evenement = validated_data["evenement"]

        if hasattr(evenement, 'places_disponibles') and evenement.places_disponibles() <= 0:
            raise serializers.ValidationError({"detail": "Événement complet"})

        inscription = Inscription.objects.create(
            participant=user,
            evenement=evenement,
            montant_paye=evenement.prix,
        )
        
        if hasattr(inscription, 'generer_reference'):
            inscription.generer_reference()
        
        # Création du paiement lié
        paiement = Paiement.objects.create(
            montant=evenement.prix,
            statut='en_attente',
            mode='stripe',
            description=f"Paiement pour {evenement.titre}"
        )
        
        inscription.paiement = paiement
        inscription.save()
        return inscription

# ================================
# BILLET
# ================================
class BilletSerializer(serializers.ModelSerializer):
    evenement_titre = serializers.CharField(source="inscription.evenement.titre", read_only=True)
    date_evenement = serializers.DateTimeField(source="inscription.evenement.date_debut", read_only=True)
    lieu = serializers.CharField(source="inscription.evenement.lieu", read_only=True)

    class Meta:
        model = Billet
        fields = [
            "id", "inscription", "qr_code", "date_emission", 
            "utilise", "evenement_titre", "date_evenement", "lieu"
        ]