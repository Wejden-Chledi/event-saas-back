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
    # Champ calculé qui retourne la liste des événements assignés au staff
    evenements_assignes = serializers.SerializerMethodField()

    firstName = serializers.CharField(source='prenom', required=False)
    lastName = serializers.CharField(source='nom', required=False)

    class Meta:

        model = Utilisateur

        # Champs qui seront exposés dans les réponses API
        fields = [
            "id", "email", "nom", "prenom", "firstName", "lastName",
            "role", "statut", "date_inscription", "telephone",
            "date_naissance", "adresse", "ville", "pays",
            "organisation", "evenements_assignes",
        ]

        # Champs non modifiables via les requêtes API
        read_only_fields = ["id", "date_inscription", "role", "organisation"]

    # Retourne la liste des événements assignés à un utilisateur
    def get_evenements_assignes(self, obj):
        # Recherche toutes les assignations du membre du staff
        assignations = AssignationEvenement.objects.filter(staff=obj)

        # Construction d'une liste contenant uniquement l'id et le titre
        return [{"id": a.evenement.id, "titre": a.evenement.titre} for a in assignations]


# ==============================
# Proprietaire + Organisation + Abonnement
# ==============================
class ProprietaireRegisterSerializer(serializers.Serializer):

    # --------------------------
    # Informations de l'utilisateur
    # --------------------------

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

    # --------------------------
    # Informations de l'organisation
    # --------------------------

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

    # --------------------------
    # Informations de l'abonnement
    # --------------------------

    type_abonnement = serializers.ChoiceField(
        choices=["gratuit", "basique", "pro", "premium"]
    )

    # --------------------------
    # VALIDATIONS
    # --------------------------

    # Vérifie que l'email n'existe pas déjà
    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    # Vérifie que les deux mots de passe sont identiques
    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs

    # --------------------------
    # CREATE
    # --------------------------

    # Création complète du propriétaire, abonnement et organisation
    def create(self, validated_data):

        # Préparation des données utilisateur
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

        # Suppression du champ de confirmation
        validated_data.pop("confirm_password")

        # Création de l'utilisateur
        user = Utilisateur.objects.create_user(**user_data)

        # Récupération du donnée
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

        # Création de l'organisation
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
        # Modèle concerné
        model = Utilisateur

        # Champs disponibles lors de l'inscription
        fields = [
            "email", "nom", "prenom", "telephone",
            "date_naissance", "adresse", "ville", "pays",
            "password", "password_confirm"
        ]

    # Vérifie l'unicité de l'email
    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    # Vérifie la correspondance des mots de passe
    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs

    # Création du participant
    def create(self, validated_data):
        # Suppression du champ de confirmation
        validated_data.pop("password_confirm")

        # Création de l'utilisateur avec le rôle participant
        return Utilisateur.objects.create_user(
            role="participant",
            statut="actif",
            **validated_data
        )


# ==============================
# Gestionnaire
# ==============================
class GestionnaireCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6, allow_blank=True)

    class Meta:
        # Modèle associé
        model = Utilisateur

        # Champs accessibles
        fields = [
            "id", "email", "nom", "prenom", "telephone",
            "date_naissance", "adresse", "ville", "pays",
            "statut", "password"
        ]
    def create(self, validated_data):

        org = validated_data.pop("organisation", self.context.get("organisation"))

        # Vérifie que l'organisation existe
        if not org:
            raise serializers.ValidationError({"organisation": "L'organisation est manquante."})
        password = validated_data.pop("password", None)
        statut = validated_data.pop("statut", "actif")

        # Création du gestionnaire
        user = Utilisateur.objects.create_user(
            role="gestionnaire",
            organisation=org,
            statut=statut,
            password=password,
            **validated_data
        )

        return user

    # Mise à jour d'un gestionnaire
    def update(self, instance, validated_data):

        # Nouveau mot de passe éventuel
        password = validated_data.pop("password", None)

        # Mise à jour du mot de passe uniquement si nécessaire
        if password and password != "********":
            instance.set_password(password)

        # Mise à jour des autres champs
        return super().update(instance, validated_data)


# ==============================
# Staff
# ==============================
class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6, allow_blank=True)

    class Meta:
        # Modèle associé
        model = Utilisateur

        # Champs accessibles
        fields = [
            "id", "email", "nom", "prenom", "telephone",
            "date_naissance", "adresse", "ville", "pays", "statut", "password"
        ]

    # Création d'un membre du staff
    def create(self, validated_data):
        org = validated_data.pop("organisation", self.context.get("organisation"))
        password = validated_data.pop("password", None)

        # Vérifie que l'organisation existe
        if not org:
            raise serializers.ValidationError({"organisation": "Organisation requise"})

        # Création du membre du staff
        return Utilisateur.objects.create_user(
            role="staff",
            organisation=org,
            statut=validated_data.pop("statut", "actif"),
            password=password,
            **validated_data
        )
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password and password != "********":
            instance.set_password(password)
        return super().update(instance, validated_data)