# apps/users/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from apps.users.models import Utilisateur, ParticipantProfile
from apps.organisations.models import Organisation, Abonnement


# ===============================
# Serializer utilisateur simple
# ===============================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "email",
            "nom",
            "prenom",
            "role",
            "statut",
            "date_inscription"
        ]


# ===============================
# Register simple utilisateur
# ===============================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = ["email", "nom", "prenom", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        if Utilisateur.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return Utilisateur.objects.create_user(
            email=validated_data["email"],
            nom=validated_data["nom"],
            prenom=validated_data["prenom"],
            password=validated_data["password"],
            role="proprietaire"
        )


# =====================================
# Register Participant + Profile
# =====================================
class ParticipantRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    date_naissance = serializers.DateField(required=False)
    adresse = serializers.CharField(required=False, allow_blank=True)
    ville = serializers.CharField(required=False, allow_blank=True)
    code_postal = serializers.CharField(required=False, allow_blank=True)
    profession = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Utilisateur
        fields = [
            "email", "nom", "prenom", "telephone",
            "password", "password_confirm",
            "date_naissance", "adresse", "ville",
            "code_postal", "profession", "bio"
        ]

    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_date_naissance(self, value):
        if value:
            today = timezone.now().date()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 18:
                raise serializers.ValidationError("Vous devez avoir au moins 18 ans.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        profile_fields = ["date_naissance", "adresse", "ville", "code_postal", "profession", "bio"]
        profile_data = {field: validated_data.pop(field, "") for field in profile_fields}

        user = Utilisateur.objects.create_user(
            email=validated_data["email"],
            nom=validated_data["nom"],
            prenom=validated_data["prenom"],
            password=validated_data["password"],
            telephone=validated_data.get("telephone", ""),
            role="participant",
            is_active=True
        )

        ParticipantProfile.objects.create(utilisateur=user, **profile_data)
        return user


# =====================================
# Register Proprietaire + Organisation
# =====================================
class ProprietaireRegisterSerializer(serializers.Serializer):
    # -------- Utilisateur --------
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    telephone = serializers.CharField(max_length=20, required=False)

    # -------- Organisation --------
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
    adresse = serializers.CharField()
    ville = serializers.CharField()
    pays = serializers.CharField()
    site_web = serializers.URLField(required=False, allow_blank=True)

    # -------- Abonnement --------
    type_abonnement = serializers.ChoiceField(
        choices=["gratuit", "basique", "pro", "premium"]
    )

    # ===============================
    # VALIDATIONS
    # ===============================
    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs

    # ===============================
    # CREATE
    # ===============================
    def create(self, validated_data):
        # -------- user data --------
        nom = validated_data.pop("nom")
        prenom = validated_data.pop("prenom")
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        validated_data.pop("confirm_password")
        telephone = validated_data.pop("telephone", "")

        user = Utilisateur.objects.create_user(
            email=email,
            nom=nom,
            prenom=prenom,
            password=password,
            telephone=telephone,
            role="proprietaire",
            is_active=True
        )

        # -------- abonnement --------
        type_abonnement = validated_data.pop("type_abonnement")
        date_debut = timezone.now().date()

        duree_mois_map = {"gratuit": 1, "basique": 1, "pro": 3, "premium": 12}
        montant_map = {"gratuit": 0, "basique": 50.0, "pro": 140.0, "premium": 500.0}

        duree_mois = duree_mois_map[type_abonnement]
        montant = montant_map[type_abonnement]
        date_fin = date_debut + timedelta(days=30 * duree_mois)

        abonnement = Abonnement.objects.create(
            type=type_abonnement,
            dateDebut=date_debut,
            dateFin=date_fin,
            montant=montant,
            statut="actif"
        )

        # -------- organisation --------
        organisation = Organisation.objects.create(
            nom=validated_data["nom_organisation"],
            secteur=validated_data["secteur"],
            emailContact=validated_data["email_contact"],
            telephone=validated_data["telephone_organisation"],
            adresse=validated_data["adresse"],
            ville=validated_data["ville"],
            pays=validated_data["pays"],
            siteWeb=validated_data.get("site_web", ""),
            proprietaire=user,
            abonnement=abonnement,
            statutAbonnement="actif"
        )

        return user