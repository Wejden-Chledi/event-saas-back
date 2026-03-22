# apps/organisations/serializers.py
from rest_framework import serializers
from .models import Organisation, Abonnement
from apps.users.serializers import UserSerializer


# ==============================
# Abonnement
# ==============================
class AbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abonnement
        fields = '__all__'
        read_only_fields = ['date_creation']


# ==============================
# Organisation simple
# ==============================
class OrganisationSerializer(serializers.ModelSerializer):

    abonnement = AbonnementSerializer(read_only=True)
    proprietaire_nom = serializers.CharField(source='proprietaire.nom', read_only=True)
    proprietaire_email = serializers.CharField(source='proprietaire.email', read_only=True)

    class Meta:
        model = Organisation
        fields = '__all__'
        read_only_fields = ['date_creation', 'proprietaire']


# ==============================
# Organisation complète
# ==============================
class OrganisationCompleteSerializer(serializers.ModelSerializer):

    abonnement = AbonnementSerializer(read_only=True)
    gestionnaires = serializers.SerializerMethodField()
    proprietaire_email = serializers.CharField(source='proprietaire.email', read_only=True)

    class Meta:
        model = Organisation
        fields = '__all__'

    def get_gestionnaires(self, obj):
        return UserSerializer(
            obj.utilisateurs.filter(role='gestionnaire'),
            many=True
        ).data


# ==============================
# Création Organisation
# ==============================
class OrganisationCreateSerializer(serializers.ModelSerializer):

    abonnement = AbonnementSerializer(required=False)

    class Meta:
        model = Organisation
        fields = [
            'nom', 'secteur', 'description', 'email_contact', 'telephone',
            'adresse', 'ville', 'pays', 'site_web', 'abonnement'
        ]

    def create(self, validated_data):

        abonnement_data = validated_data.pop('abonnement', None)
        proprietaire = self.context.get('proprietaire')

        organisation = Organisation.objects.create(
            proprietaire=proprietaire,
            **validated_data
        )

        if abonnement_data:
            abonnement = Abonnement.objects.create(**abonnement_data)
            organisation.abonnement = abonnement
            organisation.save()

        # ✅ LIAISON USER ↔ ORG
        proprietaire.organisation = organisation
        proprietaire.save()

        return organisation