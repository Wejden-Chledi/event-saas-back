from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    Evenement,
    Billet,
    Staff,
    AssignationEvenement,
    Inscription
)

Utilisateur = get_user_model()


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

        read_only_fields = [
            "createur",
            "organisation",
            "date_creation",
            "date_update",
        ]

    def get_places_disponibles(self, obj):
        return obj.places_disponibles()

    def get_est_complet(self, obj):
        return obj.est_complet()


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
            raise serializers.ValidationError(
                "La date de fin doit être après la date de début"
            )

        if date_debut < timezone.now():
            raise serializers.ValidationError(
                "La date de début ne peut pas être dans le passé"
            )

        return attrs
# ================================
# STAFF
# ================================

class StaffSerializer(serializers.ModelSerializer):

    organisation_nom = serializers.CharField(
        source="organisation.nom",
        read_only=True
    )

    evenements_assignes = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = [
            "id",
            "nom",
            "prenom",
            "email",
            "role",
            "statut",
            "organisation",
            "organisation_nom",
            "telephone",
            "date_creation",
            "evenements_assignes"
        ]

        read_only_fields = [
            "date_creation"
        ]

    def get_evenements_assignes(self, obj):

        assignations = obj.assignations.all()

        return [
            {
                "id": a.evenement.id,
                "titre": a.evenement.titre,
                "dateDebut": a.evenement.dateDebut,
                "dateFin": a.evenement.dateFin
            }
            for a in assignations
        ]


# ================================
# STAFF CREATE
# ================================

class StaffCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Staff
        fields = [
            "id",
            "nom",
            "prenom",
            "email",
            "password",
            "password_confirm",
            "telephone"
        ]

    def validate(self, attrs):

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                "Les mots de passe ne correspondent pas"
            )

        return attrs

    def create(self, validated_data):

        validated_data.pop("password_confirm")

        password = validated_data.pop("password")

        staff = Staff.objects.create(**validated_data)

        staff.set_password(password)

        staff.save()

        return staff
# ================================
# STAFF UPDATE
# ================================


class StaffUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Staff
        fields = [
            "nom",
            "prenom",
            "email",
            "telephone",
            "password",
            "password_confirm",
        ]

    def validate(self, attrs):
        # si password est fourni, vérifier confirmation
        if "password" in attrs or "password_confirm" in attrs:
            if attrs.get("password") != attrs.get("password_confirm"):
                raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("password_confirm", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance
# ================================
# ASSIGNATION STAFF EVENEMENT
# ================================

class AssignationEvenementSerializer(serializers.ModelSerializer):

    staff_nom = serializers.CharField(source="staff.nom", read_only=True)

    evenement_titre = serializers.CharField(
        source="evenement.titre",
        read_only=True
    )

    class Meta:
        model = AssignationEvenement
        fields = [
            "id",
            "staff",
            "evenement",
            "date_assignation",
            "est_actif",
            "staff_nom",
            "evenement_titre",
        ]

        read_only_fields = ["date_assignation"]



# ================================
# INSCRIPTION
# ================================
class InscriptionSerializer(serializers.ModelSerializer):

    participant_nom = serializers.CharField(source="participant.nom", read_only=True)
    participant_prenom = serializers.CharField(source="participant.prenom", read_only=True)
    evenement_titre = serializers.CharField(source="evenement.titre", read_only=True)

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
            "participant_nom",
            "participant_prenom",
            "evenement_titre",
        ]
        read_only_fields = ["date_inscription", "reference_paiement"]


# ================================
# BILLET
# ================================
class BilletSerializer(serializers.ModelSerializer):

    inscription_details = serializers.SerializerMethodField()

    class Meta:
        model = Billet
        fields = [
            "id",
            "inscription",
            "code",
            "date_emission",
            "utilise",
            "date_utilisation",
            "inscription_details"
        ]
        read_only_fields = ["code", "date_emission", "date_utilisation"]

    def get_inscription_details(self, obj):
        if obj.inscription:
            return {
                "evenement_titre": obj.inscription.evenement.titre,
                "participant_nom": obj.inscription.participant.nom,
                "participant_prenom": obj.inscription.participant.prenom,
                "date_evenement": obj.inscription.evenement.date_debut,
                "lieu": obj.inscription.evenement.lieu
            }
        return None