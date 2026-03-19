from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Utilisateur
from apps.organisations.models import Organisation, Abonnement


# ==============================
# Serializer simple utilisateur
# ==============================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = [
            "id", "email", "nom", "prenom", "role", "statut",
            "date_inscription", "telephone", "date_naissance",
            "adresse", "ville", "pays", "organisation",
        ]
        read_only_fields = ["id", "date_inscription", "role", "organisation"]


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

    class Meta:
        model = Utilisateur
        fields = [
            "email", "nom", "prenom", "telephone",
            "date_naissance", "adresse", "ville", "pays", "statut"
        ]

    def create(self, validated_data):
        org = self.context["organisation"]

        return Utilisateur.objects.create_user(
            role="gestionnaire",
            organisation=org,
            statut=validated_data.get("statut", "actif"),
            **validated_data
        )


# ==============================
# Staff
# ==============================
class StaffCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Utilisateur
        fields = [
            "email", "nom", "prenom", "telephone",
            "date_naissance", "adresse", "ville", "pays", "statut"
        ]

    def create(self, validated_data):
        org = self.context["organisation"]

        return Utilisateur.objects.create_user(
            role="staff",
            organisation=org,
            statut=validated_data.get("statut", "actif"),
            **validated_data
        )