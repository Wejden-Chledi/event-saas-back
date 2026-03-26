# apps/users/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from apps.events.models import AssignationEvenement
from .models import Utilisateur
from apps.organisations.models import Organisation, Abonnement


# ==============================
# Serializer simple utilisateur
# ==============================
class UserSerializer(serializers.ModelSerializer):
    evenements_assignes = serializers.SerializerMethodField()
    
    # Utilisez 'prenom' et 'nom' comme base, 
    # mais gardez firstName/lastName pour la cohérence Front
    firstName = serializers.CharField(source='prenom', required=False)
    lastName = serializers.CharField(source='nom', required=False)

    class Meta:
        model = Utilisateur
        fields = [
            "id", "email", "nom", "prenom", "firstName", "lastName", 
            "role", "statut", "date_inscription", "telephone", 
            "date_naissance", "adresse", "ville", "pays", 
            "organisation", "evenements_assignes",
        ]
        read_only_fields = ["id", "date_inscription", "role", "organisation"]

    def get_evenements_assignes(self, obj):
        assignations = AssignationEvenement.objects.filter(staff=obj)
        return [{"id": a.evenement.id, "titre": a.evenement.titre} for a in assignations]
# ==============================
# Proprietaire + Organisation + Abonnement
# ==============================
class ProprietaireRegisterSerializer(serializers.Serializer):

    # USER
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    telephone = serializers.CharField(max_length=20, required=False)
    date_naissance = serializers.DateField(required=False)
    adresse = serializers.CharField(required=False)
    ville = serializers.CharField(required=False)
    pays = serializers.CharField(required=False)

    # ORGANISATION
    nom_organisation = serializers.CharField(max_length=200)
    secteur = serializers.ChoiceField(choices=[
        ("technologie", "Technologie"),
        ("finance", "Finance"),
        ("sante", "Santé"),
        ("education", "Éducation"),
        ("commerce", "Commerce"),
        ("autre", "Autre"),
    ])

    email_contact = serializers.EmailField()
    telephone_organisation = serializers.CharField(max_length=20)
    adresse_org = serializers.CharField()
    ville_org = serializers.CharField()
    pays_org = serializers.CharField()
    site_web = serializers.URLField(required=False, allow_blank=True)

    # ABONNEMENT
    type_abonnement = serializers.ChoiceField(
        choices=["gratuit", "basique", "pro", "premium"]
    )

    # --------------------------
    # VALIDATIONS
    # --------------------------
    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs

    # --------------------------
    # CREATE
    # --------------------------
    def create(self, validated_data):

        # USER
        user_data = {
            "nom": validated_data.pop("nom"),
            "prenom": validated_data.pop("prenom"),
            "email": validated_data.pop("email"),
            "password": validated_data.pop("password"),
            "telephone": validated_data.pop("telephone", ""),
            "date_naissance": validated_data.pop("date_naissance", None),
            "adresse": validated_data.pop("adresse", ""),
            "ville": validated_data.pop("ville", ""),
            "pays": validated_data.pop("pays", ""),
            "role": "proprietaire",
            "statut": "actif"
        }

        validated_data.pop("confirm_password")
        user = Utilisateur.objects.create_user(**user_data)

        # ABONNEMENT
        type_abonnement = validated_data.pop("type_abonnement")

        duree_map = {
            "gratuit": 30,
            "basique": 30,
            "pro": 90,
            "premium": 365
        }

        montant_map = {
            "gratuit": 0,
            "basique": 50,
            "pro": 140,
            "premium": 500
        }

        date_debut = timezone.now().date()
        date_fin = date_debut + timedelta(days=duree_map[type_abonnement])

        abonnement = Abonnement.objects.create(
            plan=type_abonnement,
            date_debut=date_debut,
            date_fin=date_fin,
            statut="actif",
            montant=montant_map[type_abonnement]
        )

        # ORGANISATION
        organisation = Organisation.objects.create(
            nom=validated_data["nom_organisation"],
            secteur=validated_data["secteur"],
            email_contact=validated_data["email_contact"],
            telephone=validated_data["telephone_organisation"],
            adresse=validated_data["adresse_org"],
            ville=validated_data["ville_org"],
            pays=validated_data["pays_org"],
            site_web=validated_data.get("site_web", ""),
            proprietaire=user,
            abonnement=abonnement
        )

        # ✅ LIAISON IMPORTANTE
        user.organisation = organisation
        user.save()

        return user


# ==============================
# Participant
# ==============================
class ParticipantRegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = [
            "email", "nom", "prenom", "telephone",
            "date_naissance", "adresse", "ville", "pays",
            "password", "password_confirm"
        ]

    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        return Utilisateur.objects.create_user(
            role="participant",
            statut="actif",
            **validated_data
        )

# ==============================
# Gestionnaire
# ==============================
class GestionnaireCreateSerializer(serializers.ModelSerializer):
    # Password optionnel pour permettre l'update sans changer le mot de passe
    password = serializers.CharField(write_only=True, required=False, min_length=6, allow_blank=True)

    class Meta:
        model = Utilisateur
        fields = [
            "id", "email", "nom", "prenom", "telephone",
            "date_naissance", "adresse", "ville", "pays",
            "statut", "password"
        ]

    def create(self, validated_data):
        # Récupération sécurisée de l'organisation
        org = validated_data.pop("organisation", self.context.get("organisation"))
        
        if not org:
            raise serializers.ValidationError({"organisation": "L'organisation est manquante."})

        password = validated_data.pop("password", None)
        statut = validated_data.pop("statut", "actif")

        user = Utilisateur.objects.create_user(
            role="gestionnaire",
            organisation=org,
            statut=statut,
            password=password,
            **validated_data
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        # Si un nouveau password est fourni et n'est pas vide (ou les étoiles du front)
        if password and password != "********":
            instance.set_password(password)
        
        return super().update(instance, validated_data)

# ==============================
# Staff
# ==============================
class StaffCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = [
            "id", "email", "nom", "prenom", "telephone",
            "date_naissance", "adresse", "ville", "pays", "statut"
        ]

    def create(self, validated_data):
        org = validated_data.pop("organisation", self.context.get("organisation"))
        
        return Utilisateur.objects.create_user(
            role="staff",
            organisation=org,
            statut=validated_data.get("statut", "actif"),
            **validated_data
        )