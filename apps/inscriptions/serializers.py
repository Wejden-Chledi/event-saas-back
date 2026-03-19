# apps/inscriptions/serializers.py
from rest_framework import serializers
from .models import Inscription, Billet
from apps.payments.models import Paiement

# ================================
# INSCRIPTION
# ================================
class InscriptionSerializer(serializers.ModelSerializer):
    participant_nom = serializers.CharField(source="participant.nom", read_only=True)
    participant_prenom = serializers.CharField(source="participant.prenom", read_only=True)
    evenement_titre = serializers.CharField(source="evenement.titre", read_only=True)
    evenement_prix = serializers.DecimalField(source="evenement.prix", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Inscription
        fields = [
            "id",
            "participant",
            "evenement",
            "date_inscription",
            "statut",
            "montant_paye",
            "reference_paiement",
            "paiement",
            "participant_nom",
            "participant_prenom",
            "evenement_titre",
            "evenement_prix",
        ]
        read_only_fields = [
            "date_inscription",
            "reference_paiement",
            "montant_paye",
            "statut",
        ]

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

        # Vérification places disponibles
        if evenement.places_disponibles() <= 0:
            raise serializers.ValidationError("Événement complet")

        # Création de l'inscription
        inscription = Inscription.objects.create(
            participant=user,
            evenement=evenement,
            montant_paye=evenement.prix,
        )
        inscription.generer_reference()
        inscription.save()

        # Création automatique du paiement
        paiement = Paiement.objects.create(
            montant=evenement.prix,
            statut='en_attente',
            mode='stripe',
            description=f"Paiement pour l'inscription {inscription.id}"
        )
        inscription.paiement = paiement
        inscription.save()

        return inscription

# ================================
# BILLET
# ================================
class BilletSerializer(serializers.ModelSerializer):
    evenement = serializers.CharField(source="inscription.evenement.titre", read_only=True)
    participant = serializers.CharField(source="inscription.participant.email", read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Billet
        fields = [
            "id",
            "inscription",
            "qr_code",
            "pdf_url",
            "date_emission",
            "utilise",
            "date_utilisation",
            "evenement",
            "participant",
        ]
        read_only_fields = [
            "qr_code",
            "date_emission",
            "date_utilisation",
            "pdf_url",
        ]

    def get_pdf_url(self, obj):
        if hasattr(obj, 'pdf_file') and obj.pdf_file:
            return obj.pdf_file.url
        return None