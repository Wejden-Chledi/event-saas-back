# apps/events/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Evenement, AssignationEvenement, EventPhoto
from .ai_service import generate_event_description as gen_desc

class EventPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventPhoto
        fields = ['id', 'image', 'uploaded_at']

class EvenementSerializer(serializers.ModelSerializer):
    # Champs calculés ou liés en lecture seule
    createur_nom = serializers.CharField(source="createur.nom", read_only=True)
    organisation_nom = serializers.CharField(source="organisation.nom", read_only=True)
    places_disponibles = serializers.IntegerField(read_only=True)
    est_complet = serializers.BooleanField(read_only=True)
    photos = EventPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Evenement
        fields = [
            "id", "titre", "description", "lieu", "date_debut", "date_fin",
            "capacite_max", "prix", "statut", "organisation", "organisation_nom",
            "createur", "createur_nom", "date_creation", "date_update",
            "places_disponibles", "est_complet", "photos", "image_principale"  # Ajouté pour l'image de couverture
        ]
        read_only_fields = ["createur", "organisation", "date_creation", "date_update"]

    def validate(self, attrs):
        """Validation centralisée des dates et capacités"""
        # On récupère les valeurs (nouvelles ou existantes si UPDATE)
        instance = self.instance
        date_debut = attrs.get("date_debut", getattr(instance, 'date_debut', None))
        date_fin = attrs.get("date_fin", getattr(instance, 'date_fin', None))
        capacite = attrs.get("capacite_max", getattr(instance, 'capacite_max', None))

        # 1. Logique des dates
        if date_debut and date_fin and date_debut >= date_fin:
            raise serializers.ValidationError({"date_fin": "La date de fin doit être après le début."})
        
        if date_debut and date_debut < timezone.now() and not instance:
            raise serializers.ValidationError({"date_debut": "Impossible de créer un événement dans le passé."})

        # 2. Logique de capacité (si update)
        if instance and capacite:
            inscriptions_payees = instance.inscriptions.filter(statut="paye").count()
            if capacite < inscriptions_payees:
                raise serializers.ValidationError(
                    {"capacite_max": f"Capacité minimale requise : {inscriptions_payees} (déjà payés)."}
                )

        return attrs

    def create(self, validated_data):
        """Intégration automatique de l'IA à la création"""
        if not validated_data.get("description"):
            titre = validated_data.get("titre")
            try:
                validated_data["description"] = gen_desc(titre)
            except Exception:
                validated_data["description"] = "Description en attente de génération..."
        
        return super().create(validated_data)

class AssignationEvenementSerializer(serializers.ModelSerializer):
    staff_nom_complet = serializers.SerializerMethodField()
    evenement_titre = serializers.CharField(source="evenement.titre", read_only=True)

    class Meta:
        model = AssignationEvenement
        fields = ['id', 'staff', 'evenement', 'staff_nom_complet', 'evenement_titre', 'date_assignation']

    def get_staff_nom_complet(self, obj):
        return f"{obj.staff.nom} {obj.staff.prenom}"