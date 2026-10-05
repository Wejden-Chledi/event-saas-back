# ============================================================================
# Fichier : apps/organisations/serializers.py
#
# Ce fichier contient les serializers liés aux organisations.
#
# Les serializers permettent de :
#
#   - transformer les objets Django (Models) en JSON ;
#   - valider les données reçues par l'API ;
#   - gérer la création et la modification des organisations.
#
# Ce fichier contient :
#
#   - AbonnementSerializer :
#       Gestion de la sérialisation des abonnements.
#
#   - OrganisationSerializer :
#       Affichage simple d'une organisation.
#
#   - OrganisationCompleteSerializer :
#       Affichage détaillé avec les gestionnaires.
#
#   - OrganisationCreateSerializer :
#       Création personnalisée d'une organisation
#       avec son abonnement et son propriétaire.
# ============================================================================


# ==============================
# IMPORTATION DES LIBRAIRIES
# ==============================

# Module serializers de Django REST Framework.
# Il fournit les classes nécessaires pour créer
# des serializers.
from rest_framework import serializers


# Importation des modèles Organisation et Abonnement.
from .models import Organisation, Abonnement


# Serializer utilisateur utilisé pour afficher
# les informations des gestionnaires.
from apps.users.serializers import UserSerializer



# ============================================================================
# SERIALIZER : ABONNEMENT
# ============================================================================
#
# Permet de convertir un objet Abonnement en JSON
# et de valider les données liées à un abonnement.
# ============================================================================

class AbonnementSerializer(serializers.ModelSerializer):

    class Meta:

        # Modèle Django associé.
        model = Abonnement


        # Utilisation de tous les champs du modèle.
        fields = '__all__'


        # Champs accessibles uniquement en lecture.
        #
        # La date de création est générée automatiquement
        # par Django et ne doit pas être modifiée par l'utilisateur.
        read_only_fields = [
            'date_creation'
        ]



# ============================================================================
# SERIALIZER : ORGANISATION SIMPLE
# ============================================================================
#
# Serializer utilisé pour afficher les informations
# principales d'une organisation.
#
# Il inclut également :
#   - les informations de l'abonnement ;
#   - le nom du propriétaire.
# ============================================================================

class OrganisationSerializer(serializers.ModelSerializer):


    # Sérialisation imbriquée de l'abonnement.
    #
    # read_only=True signifie que l'abonnement
    # est uniquement affiché et ne peut pas être modifié ici.
    abonnement = AbonnementSerializer(
        read_only=True
    )


    # Récupération du nom du propriétaire.
    #
    # source indique le chemin vers l'attribut :
    #
    # Organisation
    #       |
    #       --> proprietaire
    #              |
    #              --> nom
    #
    proprietaire_nom = serializers.CharField(
        source='proprietaire.nom',
        read_only=True
    )


    class Meta:

        # Modèle associé.
        model = Organisation


        # Retourne tous les champs du modèle.
        fields = '__all__'


        # Champs protégés contre la modification.
        read_only_fields = [
            'date_creation',
            'proprietaire'
        ]



# ============================================================================
# SERIALIZER : ORGANISATION COMPLETE
# ============================================================================
#
# Version détaillée d'une organisation.
#
# Elle ajoute la liste des gestionnaires appartenant
# à cette organisation.
# ============================================================================

class OrganisationCompleteSerializer(serializers.ModelSerializer):


    # Affichage de l'abonnement associé.
    abonnement = AbonnementSerializer(
        read_only=True
    )


    # Champ calculé dynamiquement.
    #
    # SerializerMethodField permet de créer
    # une donnée personnalisée.
    gestionnaires = serializers.SerializerMethodField()



    class Meta:

        model = Organisation

        fields = '__all__'



    # ------------------------------------------------------------------------
    # Récupération des gestionnaires.
    #
    # Cette méthode est automatiquement appelée
    # par DRF grâce au champ :
    #
    # gestionnaires = SerializerMethodField()
    #
    # Elle retourne uniquement les utilisateurs
    # ayant le rôle "gestionnaire".
    # ------------------------------------------------------------------------
    def get_gestionnaires(self, obj):

        return UserSerializer(
            obj.utilisateurs.filter(
                role='gestionnaire'
            ),
            many=True
        ).data



# ============================================================================
# SERIALIZER : CREATION D'UNE ORGANISATION
# ============================================================================
#
# Serializer utilisé uniquement lors de la création
# d'une organisation.
#
# Il contient une logique métier personnalisée :
#
#   - création de l'organisation ;
#   - création de l'abonnement ;
#   - association avec le propriétaire.
# ============================================================================

class OrganisationCreateSerializer(serializers.ModelSerializer):


    # L'abonnement est optionnel lors de la création.
    abonnement = AbonnementSerializer(
        required=False
    )


    class Meta:

        # Modèle concerné.
        model = Organisation


        # Champs autorisés lors de la création.
        fields = [
            'nom',
            'secteur',
            'description',
            'email_contact',
            'telephone',
            'adresse',
            'ville',
            'pays',
            'site_web',
            'abonnement'
        ]



    # ------------------------------------------------------------------------
    # Méthode create personnalisée.
    #
    # Elle remplace le comportement par défaut
    # de ModelSerializer.create().
    #
    # Elle permet de gérer :
    #
    #   - le propriétaire injecté depuis la vue ;
    #   - l'abonnement associé ;
    #   - la relation utilisateur <-> organisation.
    # ------------------------------------------------------------------------

    def create(self, validated_data):


        # --------------------------------------------------------------------
        # 1. Récupération du propriétaire.
        #
        # Le propriétaire peut être envoyé depuis :
        #
        # serializer.save(proprietaire=...)
        #
        # ou depuis le contexte du serializer.
        # --------------------------------------------------------------------

        proprietaire = validated_data.pop(
            'proprietaire',
            self.context.get('proprietaire')
        )



        # --------------------------------------------------------------------
        # 2. Extraction des données d'abonnement.
        #
        # Elles sont séparées car l'abonnement
        # possède son propre modèle.
        # --------------------------------------------------------------------

        abonnement_data = validated_data.pop(
            'abonnement',
            None
        )



        # --------------------------------------------------------------------
        # 3. Création de l'organisation.
        #
        # Le propriétaire est ajouté explicitement
        # pour créer correctement la relation ForeignKey.
        # --------------------------------------------------------------------

        organisation = Organisation.objects.create(
            proprietaire=proprietaire,
            **validated_data
        )



        # --------------------------------------------------------------------
        # 4. Création de l'abonnement.
        #
        # Si des données d'abonnement existent :
        #   - création de l'objet Abonnement ;
        #   - association avec l'organisation.
        # --------------------------------------------------------------------

        if abonnement_data:

            abonnement = Abonnement.objects.create(
                **abonnement_data
            )

            organisation.abonnement = abonnement

            organisation.save()



        # --------------------------------------------------------------------
        # 5. Association de l'organisation au propriétaire.
        #
        # Après création :
        # utilisateur.organisation = organisation
        #
        # Cette relation permet de retrouver
        # facilement l'organisation d'un utilisateur.
        # --------------------------------------------------------------------

        if proprietaire:

            proprietaire.organisation = organisation

            proprietaire.save()



        # Retourne l'organisation créée.
        return organisation