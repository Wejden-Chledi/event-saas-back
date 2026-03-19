from rest_framework import serializers
from django.utils import timezone
from apps.events.models import Evenement, AssignationEvenement, EventPhoto
from apps.events.ai_service import generate_event_description as gen_desc  # ton service IA

# ================================
# EVENEMENT
# ================================
class EvenementSerializer(serializers.ModelSerializer):
    createur_nom = serializers.CharField(source="createur.nom", read_only=True)
    createur_prenom = serializers.CharField(source="createur.prenom", read_only=True)
    organisation_nom = serializers.CharField(source="organisation.nom", read_only=True)
    places_disponibles = serializers.SerializerMethodField()
    est_complet = serializers.SerializerMethodField()

    class Meta:
        model = Evenement
        fields = [
            "id",
            "titre",
            "description",
            "lieu",
            "date_debut",
            "date_fin",
            "capacite_max",
            "prix",
            "statut",
            "organisation",
            "organisation_nom",
            "createur",
            "createur_nom",
            "createur_prenom",
            "date_creation",
            "date_update",
            "places_disponibles",
            "est_complet",
        ]
        read_only_fields = ["createur", "organisation", "date_creation", "date_update"]

    def get_places_disponibles(self, obj):
        return obj.places_disponibles()

    def get_est_complet(self, obj):
        return obj.est_complet()


# ================================
# CREATE EVENEMENT (IA intégrée)
# ================================
class EvenementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evenement
        fields = [
            "titre",
            "description",
            "lieu",
            "date_debut",
            "date_fin",
            "capacite_max",
            "prix",
        ]

    def validate(self, attrs):
        date_debut = attrs.get("date_debut")
        date_fin = attrs.get("date_fin")

        if date_debut >= date_fin:
            raise serializers.ValidationError("La date de fin doit être après la date de début")

        if date_debut < timezone.now():
            raise serializers.ValidationError("La date de début ne peut pas être dans le passé")

        return attrs

    def create(self, validated_data):
        # Si la description est vide, générer avec IA
        if not validated_data.get("description"):
            titre = validated_data.get("titre")
            validated_data["description"] = gen_desc(titre)
        return super().create(validated_data)


# ================================
# UPDATE EVENEMENT
# ================================
class EvenementUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evenement
        fields = [
            "titre",
            "description",
            "lieu",
            "date_debut",
            "date_fin",
            "capacite_max",
            "prix",
            "statut",
        ]

    def validate_capacite_max(self, value):
        evenement = self.instance
        inscriptions_payees = evenement.inscriptions.filter(statut="paye").count()
        if value < inscriptions_payees:
            raise serializers.ValidationError(
                f"Capacité minimale {inscriptions_payees} (déjà inscrit et payé)."
            )
        return value

    def validate(self, attrs):
        date_debut = attrs.get("date_debut", self.instance.date_debut)
        date_fin = attrs.get("date_fin", self.instance.date_fin)
        if date_debut >= date_fin:
            raise serializers.ValidationError("La date de fin doit être après la date de début")
        if date_debut < timezone.now():
            raise serializers.ValidationError("La date de début ne peut pas être dans le passé")
        return attrs


# ================================
# ASSIGNATION STAFF À ÉVÉNEMENT
# ================================
class AssignationEvenementSerializer(serializers.ModelSerializer):
    staff_nom = serializers.CharField(source="staff.nom", read_only=True)
    staff_prenom = serializers.CharField(source="staff.prenom", read_only=True)
    organisation_id = serializers.IntegerField(source="staff.organisation.id", read_only=True)
    organisation_nom = serializers.CharField(source="staff.organisation.nom", read_only=True)
    evenement_titre = serializers.CharField(source="evenement.titre", read_only=True)

    class Meta:
        model = AssignationEvenement
        fields = [
            "id",
            "staff",
            "evenement",
            "date_assignation",
            "staff_nom",
            "staff_prenom",
            "organisation_id",
            "organisation_nom",
            "evenement_titre",
        ]
        read_only_fields = ["date_assignation"]


# ================================
# PHOTOS D'ÉVÉNEMENT
# ================================
class EventPhotoSerializer(serializers.ModelSerializer):
    evenement_titre = serializers.CharField(source="evenement.titre", read_only=True)

    class Meta:
        model = EventPhoto
        fields = [
            "id",
            "evenement",
            "evenement_titre",
            "image",
            "uploaded_at",
        ]
        read_only_fields = ["uploaded_at"]