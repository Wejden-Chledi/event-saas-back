# apps/organisations/serializers.py
from rest_framework import serializers
from .models import Organisation, Abonnement
from apps.users.serializers import UserSerializer


# ======================
# ABONNEMENT
# ======================
class AbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abonnement
        fields = '__all__'
        read_only_fields = ['date_creation']


# ======================
# ORGANISATION SIMPLE
# ======================
class OrganisationSerializer(serializers.ModelSerializer):

    abonnement = AbonnementSerializer(read_only=True)

    proprietaire_nom = serializers.CharField(
        source='proprietaire.nom',
        read_only=True
    )

    class Meta:
        model = Organisation
        fields = '__all__'
        read_only_fields = ['date_creation', 'proprietaire']


# ======================
# ORGANISATION COMPLETE
# ======================
class OrganisationCompleteSerializer(serializers.ModelSerializer):

    abonnement = AbonnementSerializer(read_only=True)

    gestionnaires = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = '__all__'

    def get_gestionnaires(self, obj):
        return UserSerializer(
            obj.utilisateurs.filter(role='gestionnaire'),
            many=True
        ).data


# ======================
# CREATE ORGANISATION FIXED
# ======================
# apps/organisations/serializers.py

class OrganisationCreateSerializer(serializers.ModelSerializer):
    abonnement = AbonnementSerializer(required=False)

    class Meta:
        model = Organisation
        fields = [
            'nom', 'secteur', 'description',
            'email_contact', 'telephone',
            'adresse', 'ville', 'pays',
            'site_web', 'abonnement'
        ]

    # apps/organisations/serializers.py

    def create(self, validated_data):
        # 1. Extraire le propriétaire injecté par serializer.save(proprietaire=...)
        # Si non présent (cas de certains tests unitaires), on regarde dans le contexte
        proprietaire = validated_data.pop('proprietaire', self.context.get('proprietaire'))
        
        # 2. Extraire les données d'abonnement
        abonnement_data = validated_data.pop('abonnement', None)

        # 3. Créer l'organisation
        # Maintenant 'validated_data' ne contient plus 'proprietaire', donc pas de doublon
        organisation = Organisation.objects.create(
            proprietaire=proprietaire, 
            **validated_data
        )

        # 4. Gérer l'abonnement
        if abonnement_data:
            abonnement = Abonnement.objects.create(**abonnement_data)
            organisation.abonnement = abonnement
            organisation.save()

        # 5. Lier l'organisation à l'utilisateur
        if proprietaire:
            proprietaire.organisation = organisation
            proprietaire.save()

        return organisation