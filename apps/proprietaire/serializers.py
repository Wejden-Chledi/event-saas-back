# src/apps/proprietaire/serializers.py

from rest_framework import serializers
from .models import InformationOrganisation, Gestionnaire, DemandeAbonnement
from apps.organisations.models import Organisation
from apps.users.models import Utilisateur


# ================================
# InformationOrganisation Serializer
# ================================
class InformationOrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformationOrganisation
        fields = '__all__'
        read_only_fields = ['date_mise_a_jour']


# ================================
# Gestionnaire Serializer
# ================================
class GestionnaireSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.nom', read_only=True)
    utilisateur_prenom = serializers.CharField(source='utilisateur.prenom', read_only=True)
    utilisateur_email = serializers.CharField(source='utilisateur.email', read_only=True)
    utilisateur_telephone = serializers.CharField(source='utilisateur.telephone', read_only=True)

    statut = serializers.SerializerMethodField()
    statut_input = serializers.CharField(write_only=True, required=False)

    # Champs modifiables pour mise à jour utilisateur
    nom = serializers.CharField(write_only=True, required=False)
    prenom = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    telephone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Gestionnaire
        fields = '__all__'
        read_only_fields = ['organisation', 'date_creation']

    def get_statut(self, obj):
        return "active" if obj.actif else "inactive"

    def update(self, instance, validated_data):
        # Récupération des champs utilisateur
        nom = validated_data.pop('nom', None)
        prenom = validated_data.pop('prenom', None)
        email = validated_data.pop('email', None)
        telephone = validated_data.pop('telephone', None)
        password = validated_data.pop('password', None)
        password_confirm = validated_data.pop('password_confirm', None)
        statut_input = validated_data.pop('statut_input', None)

        instance = super().update(instance, validated_data)
        utilisateur = instance.utilisateur

        if nom:
            utilisateur.nom = nom
        if prenom:
            utilisateur.prenom = prenom
        if email:
            utilisateur.email = email
        if telephone:
            utilisateur.telephone = telephone
        if password and password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({
                    "password_confirm": ["Les mots de passe ne correspondent pas"]
                })
            utilisateur.set_password(password)

        utilisateur.save()

        if statut_input:
            instance.actif = True if statut_input.lower() == "active" else False
            instance.save()

        return instance


# ================================
# GestionnaireCreateSerializer
# ================================
class GestionnaireCreateSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(write_only=True)
    prenom = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    telephone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    statut = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Gestionnaire
        fields = ['nom', 'prenom', 'email', 'telephone', 'password', 'password_confirm', 'statut']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": ["Les mots de passe ne correspondent pas"]
            })
        return attrs

    def create(self, validated_data):
        nom = validated_data.pop('nom')
        prenom = validated_data.pop('prenom')
        email = validated_data.pop('email')
        telephone = validated_data.pop('telephone', '')
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)
        statut_input = validated_data.pop('statut', 'inactive')

        request = self.context.get("request")
        organisation = None
        if request and hasattr(request.user, 'organisation_proprietaire'):
            organisation = request.user.organisation_proprietaire
        else:
            organisation = Organisation.objects.get(proprietaire=request.user)

        utilisateur = Utilisateur.objects.create_user(
            email=email,
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            password=password,
            role='gestionnaire',
            is_active=True
        )

        gestionnaire = Gestionnaire.objects.create(
            utilisateur=utilisateur,
            organisation=organisation,
            actif=True if statut_input.lower() == "active" else False
        )

        return gestionnaire


# ================================
# DemandeAbonnement Serializer
# ================================
class DemandeAbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeAbonnement
        fields = '__all__'
        read_only_fields = [
            'organisation',
            'date_demande',
            'statut',
            'date_traitement',
            'commentaire_admin',
            'montant_propose'
        ]


# ================================
# OrganisationComplete Serializer
# ================================
class OrganisationCompleteSerializer(serializers.ModelSerializer):
    informations = InformationOrganisationSerializer(read_only=True)
    gestionnaires = GestionnaireSerializer(many=True, read_only=True)
    abonnement = serializers.SerializerMethodField()
    proprietaire_email = serializers.CharField(source='proprietaire.email', read_only=True)

    class Meta:
        model = Organisation
        fields = '__all__'

    def get_abonnement(self, obj):
        if obj.abonnement:
            return {
                'type': obj.abonnement.type,
                'statut': obj.abonnement.statut,
                'dateDebut': obj.abonnement.dateDebut,
                'dateFin': obj.abonnement.dateFin,
                'montant': obj.abonnement.montant
            }
        return None


# ================================
# ChangerAbonnement Serializer
# ================================
class ChangerAbonnementSerializer(serializers.Serializer):
    TYPE_CHOICES = [
        ('gratuit', 'Gratuit'),
        ('basique', 'Basique'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    ]
    type = serializers.ChoiceField(choices=TYPE_CHOICES)
    raison = serializers.CharField(max_length=500, required=False)
    montant_propose = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    def validate(self, attrs):
        tarifs = {
        'gratuit': 0,
        'basique': 50.0,
        'pro': 140.0,
        'premium': 500.0,
        }
        attrs['montant_propose'] = tarifs.get(attrs['type'], 0)
        return attrs