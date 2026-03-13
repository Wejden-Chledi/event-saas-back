from rest_framework import serializers
from django.utils import timezone
from .models import InformationOrganisation, Gestionnaire, DemandeAbonnement
from apps.organisations.models import Organisation
from apps.users.models import Utilisateur


class InformationOrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformationOrganisation
        fields = '__all__'
        read_only_fields = ['date_mise_a_jour']


class GestionnaireSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.nom', read_only=True)
    utilisateur_prenom = serializers.CharField(source='utilisateur.prenom', read_only=True)
    utilisateur_email = serializers.CharField(source='utilisateur.email', read_only=True)
    utilisateur_telephone = serializers.CharField(source='utilisateur.telephone', read_only=True)
    
    nom = serializers.CharField(write_only=True, required=False)
    prenom = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    telephone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Gestionnaire
        fields = '__all__'
        read_only_fields = ['organisation']

    def update(self, instance, validated_data):
        nom = validated_data.pop('nom', None)
        prenom = validated_data.pop('prenom', None)
        email = validated_data.pop('email', None)
        telephone = validated_data.pop('telephone', None)
        password = validated_data.pop('password', None)
        password_confirm = validated_data.pop('password_confirm', None)
        
        instance = super().update(instance, validated_data)
        utilisateur = instance.utilisateur
        
        if nom: utilisateur.nom = nom
        if prenom: utilisateur.prenom = prenom
        if email: utilisateur.email = email
        if telephone: utilisateur.telephone = telephone
        
        if password and password_confirm:
            if password == password_confirm:
                utilisateur.set_password(password)
            else:
                raise serializers.ValidationError({"password_confirm": ["Les mots de passe ne correspondent pas"]})
        
        utilisateur.save()
        return instance


class GestionnaireCreateSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(write_only=True)
    prenom = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    telephone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Gestionnaire
        fields = ['nom', 'prenom', 'email', 'telephone', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": ["Les mots de passe ne correspondent pas"]})
        return attrs
    
    def create(self, validated_data):
        nom = validated_data.pop('nom')
        prenom = validated_data.pop('prenom')
        email = validated_data.pop('email')
        telephone = validated_data.pop('telephone', '')
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)
        
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
            poste='Gestionnaire',
            date_embauche=timezone.now().date(),
            **validated_data
        )
        return gestionnaire


class DemandeAbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeAbonnement
        fields = '__all__'
        read_only_fields = ['organisation', 'date_demande', 'statut', 'date_traitement', 'commentaire_admin']


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


class ChangerAbonnementSerializer(serializers.Serializer):
    TYPE_CHOICES = [('mensuel', 'Mensuel'), ('trimestriel', 'Trimestriel'), ('annuel', 'Annuel')]
    
    type = serializers.ChoiceField(choices=TYPE_CHOICES)
    raison = serializers.CharField(max_length=500, required=False) 
    
    def validate(self, attrs):
        tarifs = {'mensuel': 29.99, 'trimestriel': 79.99, 'annuel': 299.99}
        attrs['montant_propose'] = tarifs.get(attrs['type'], 0)
        return attrs