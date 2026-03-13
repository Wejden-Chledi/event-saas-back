from rest_framework import serializers
from .models import Organisation, Abonnement


class AbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abonnement
        fields = '__all__'
        read_only_fields = ['dateCreation']


class OrganisationSerializer(serializers.ModelSerializer):
    abonnement = AbonnementSerializer(read_only=True)
    proprietaire_nom = serializers.CharField(source='proprietaire.nom', read_only=True)
    proprietaire_email = serializers.CharField(source='proprietaire.email', read_only=True)

    class Meta:
        model = Organisation
        fields = '__all__'
        read_only_fields = ['dateCreation', 'proprietaire']


class OrganisationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'une organisation avec abonnement"""
    abonnement = AbonnementSerializer(required=False)
    
    class Meta:
        model = Organisation
        fields = ['nom', 'secteur', 'logo', 'emailContact', 'telephone', 'adresse', 'siteWeb', 'abonnement']
    
    def create(self, validated_data):
        abonnement_data = validated_data.pop('abonnement', None)
        organisation = Organisation.objects.create(**validated_data)
        
        if abonnement_data:
            abonnement = Abonnement.objects.create(**abonnement_data)
            organisation.abonnement = abonnement
            organisation.save()
        
        return organisation
