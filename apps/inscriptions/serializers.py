# apps/inscriptions/serializers.py
from rest_framework import serializers
from django.db import transaction
from .models import Inscription, Billet
from apps.payments.models import Paiement
from rest_framework import serializers
from .models import Inscription


class BilletSerializer(serializers.ModelSerializer):
    """Serializer pour les détails du billet (utilisé par les participants et le staff)"""
    evenement_titre = serializers.CharField(source="inscription.evenement.titre", read_only=True)
    date_evenement = serializers.DateTimeField(source="inscription.evenement.date_debut", read_only=True)
    lieu = serializers.CharField(source="inscription.evenement.lieu", read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    
    # Informations sur le scan pour le staff
    scanne_par_nom = serializers.CharField(source="scanne_par.email", read_only=True)

    class Meta:
        model = Billet
        fields = [
            "id", "inscription", "qr_code_url", "date_emission", 
            "utilise", "date_scan", "scanne_par", "scanne_par_nom",
            "evenement_titre", "date_evenement", "lieu"
        ]
        read_only_fields = ["id", "date_emission", "date_scan", "scanne_par", "utilise"]

    def get_qr_code_url(self, obj):
        request = self.context.get('request')
        if obj.qr_code and request:
            return request.build_absolute_uri(obj.qr_code.url)
        return None

class InscriptionSerializer(serializers.ModelSerializer):
    """Serializer complet pour l'affichage d'une inscription"""
    participant_nom = serializers.CharField(source="participant.nom", read_only=True)
    participant_prenom = serializers.CharField(source="participant.prenom", read_only=True)
    participant_email = serializers.EmailField(source="participant.email", read_only=True)
    evenement_titre = serializers.CharField(source="evenement.titre", read_only=True)
    evenement_prix = serializers.DecimalField(source="evenement.prix", max_digits=10, decimal_places=2, read_only=True)
    statut_label = serializers.CharField(source="get_statut_display", read_only=True)
    statut_paiement = serializers.CharField(source="paiement.statut", read_only=True)
    
    # Lien vers le billet si disponible
    billet = BilletSerializer(read_only=True)

    class Meta:
        model = Inscription
        fields = [
            "id", "participant", "participant_nom", "participant_prenom", "participant_email",
            "evenement", "evenement_titre", "evenement_prix", "date_inscription", 
            "statut", "statut_label", "statut_paiement", "montant_paye", 
            "reference_paiement", "paiement", "billet"
        ]
        read_only_fields = ["date_inscription", "reference_paiement", "montant_paye", "statut"]

class InscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création initiale d'une inscription (avant paiement)"""
    class Meta:
        model = Inscription
        fields = ["evenement"]

    def validate(self, data):
        user = self.context["request"].user
        evenement = data["evenement"]

        # 1. Vérifier si l'utilisateur est déjà inscrit (tous statuts confondus sauf annulé)
        if Inscription.objects.filter(participant=user, evenement=evenement).exclude(statut='annule').exists():
            raise serializers.ValidationError("Vous avez déjà une inscription en cours ou validée pour cet événement.")

        # 2. Vérifier si l'événement est complet
        if evenement.est_complet():
            raise serializers.ValidationError("Désolé, cet événement est déjà complet.")

        # 3. Vérifier si l'événement est publié
        if evenement.statut != 'publie':
            raise serializers.ValidationError("Cet événement n'est pas ouvert aux inscriptions.")

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
class CheckInSerializer(serializers.Serializer):
       billet_id = serializers.UUIDField(help_text="L'ID unique du billet (UUID)")

class ParticipantDashboardSerializer(serializers.ModelSerializer):
    prenom = serializers.CharField(source='participant.prenom', read_only=True)
    nom = serializers.CharField(source='participant.nom', read_only=True)
    email = serializers.CharField(source='participant.email', read_only=True)
    
    # On va chercher l'heure du scan directement depuis le billet lié
    checkin_time = serializers.SerializerMethodField()

    class Meta:
        model = Inscription
        fields = ['id', 'prenom', 'nom', 'email', 'checkin_time']

    def get_checkin_time(self, obj):
        # On vérifie si un billet existe pour cette inscription
        # On utilise hasattr car c'est une relation OneToOne inversée
        if hasattr(obj, 'billet') and obj.billet:
            if obj.billet.utilise:
                # On retourne la date du scan si le billet est utilisé
                return obj.billet.date_scan
        return None
    
    