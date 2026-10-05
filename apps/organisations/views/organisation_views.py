# ============================================================================
# Fichier : apps/organisations/views/organisation_views.py
#
# Ce fichier contient le ViewSet permettant la gestion des organisations.
#
# Fonctionnalités :
#
#   - Création d'une organisation par un propriétaire
#   - Consultation d'une organisation
#   - Modification des informations d'une organisation
#   - Récupération de l'organisation de l'utilisateur connecté (me)
#   - Affichage des statistiques de l'organisation (stats)
#
# Les droits d'accès dépendent du rôle :
#
#   - Propriétaire :
#       création et modification de l'organisation
#
#   - Gestionnaire :
#       consultation uniquement de son organisation
# ============================================================================



# ==============================
# IMPORTATION DES LIBRAIRIES DRF
# ==============================


# viewsets fournit ModelViewSet qui permet
# d'avoir automatiquement les opérations CRUD.
#
# status contient les codes HTTP (200, 400, 404...).
from rest_framework import viewsets, status


# Permet de créer des routes personnalisées
# dans un ViewSet.
from rest_framework.decorators import action


# Permet de retourner des réponses HTTP JSON.
from rest_framework.response import Response


# Permission nécessitant un utilisateur connecté.
from rest_framework.permissions import IsAuthenticated




# ==============================
# IMPORTATION DES PERMISSIONS
# ==============================


# Permissions personnalisées permettant
# de contrôler les accès selon le rôle.
from apps.users.permissions import (
    IsProprietaire,
    IsGestionnaire
)




# ==============================
# IMPORTATION DES MODELES
# ==============================


# Modèle représentant une organisation.
from ..models import Organisation




# ==============================
# IMPORTATION DES SERIALIZERS
# ==============================


# Serializers utilisés selon l'action :
#
# OrganisationSerializer :
#       affichage simple
#
# OrganisationCompleteSerializer :
#       affichage détaillé avec gestionnaires
#
# OrganisationCreateSerializer :
#       création d'une organisation
from ..serializers import (
    OrganisationSerializer,
    OrganisationCompleteSerializer,
    OrganisationCreateSerializer
)





# ============================================================================
# VIEWSET ORGANISATION
# ============================================================================

class OrganisationViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour gérer les organisations.

    Il hérite de ModelViewSet qui fournit automatiquement :

        - GET liste
        - GET détail
        - POST création
        - PUT modification
        - PATCH modification partielle
        - DELETE suppression
    """



    # ------------------------------------------------------------------------
    # Gestion dynamique des permissions
    # ------------------------------------------------------------------------

    def get_permissions(self):
        """
        Définit les permissions selon l'action demandée.

        Consultation :
            - list
            - retrieve
            - me
            - stats

        Accessible par :
            - propriétaire
            - gestionnaire

        Autres actions :
            - création
            - modification
            - suppression

        Réservées au propriétaire.
        """


        if self.action in [
            'list',
            'retrieve',
            'me',
            'stats'
        ]:

            return [
                IsAuthenticated(),
                (IsProprietaire | IsGestionnaire)()
            ]


        return [
            IsAuthenticated(),
            IsProprietaire()
        ]




    # ------------------------------------------------------------------------
    # Filtrage des organisations accessibles
    # ------------------------------------------------------------------------

    def get_queryset(self):
        """
        Retourne uniquement les organisations
        accessibles par l'utilisateur connecté.

        Objectif :
            empêcher un utilisateur de voir
            les organisations des autres clients.
        """


        user = self.request.user



        # Vérification de l'authentification.
        if not user.is_authenticated:

            return Organisation.objects.none()



        # Cas propriétaire :
        #
        # Un propriétaire voit uniquement
        # son organisation.
        if user.role == "proprietaire":

            return Organisation.objects.filter(
                proprietaire=user
            )



        # Cas gestionnaire :
        #
        # Le gestionnaire récupère
        # l'organisation qui lui est associée.
        if hasattr(user, "organisation") and user.organisation:

            return Organisation.objects.filter(
                id=user.organisation.id
            )



        # Aucun accès si aucune organisation
        # n'est trouvée.
        return Organisation.objects.none()




    # ------------------------------------------------------------------------
    # Choix du serializer selon l'action
    # ------------------------------------------------------------------------

    def get_serializer_class(self):
        """
        Sélectionne automatiquement le serializer adapté.
        """


        # Lors de la création :
        # utilisation du serializer spécialisé.
        if self.action == "create":

            return OrganisationCreateSerializer



        # Pour afficher les détails :
        # utilisation de la version complète.
        if self.action in [
            "retrieve",
            "me"
        ]:

            return OrganisationCompleteSerializer



        # Par défaut :
        # serializer simple.
        return OrganisationSerializer





    # =========================================================================
    # CREATION ORGANISATION
    # =========================================================================

    def perform_create(self, serializer):
        """
        Ajoute automatiquement le propriétaire
        lors de la création.

        L'utilisateur connecté devient
        automatiquement le propriétaire.
        """

        serializer.save(
            proprietaire=self.request.user
        )






    # =========================================================================
    # ORGANISATION CONNECTEE : ME
    # =========================================================================

    @action(
        detail=False,
        methods=[
            'get',
            'patch',
            'put'
        ]
    )
    def me(self, request):
        """
        Retourne l'organisation liée
        à l'utilisateur connecté.

        Méthodes acceptées :

            GET :
                consulter l'organisation

            PATCH / PUT :
                modifier l'organisation
        """


        user = request.user



        # Si utilisateur propriétaire :
        # recherche par propriétaire.
        if user.role == "proprietaire":

            organisation = Organisation.objects.filter(
                proprietaire=user
            ).first()



        # Si utilisateur gestionnaire :
        # récupération via la relation organisation.
        else:

            organisation = getattr(
                user,
                "organisation",
                None
            )



        # Vérification de l'existence.
        if not organisation:

            return Response(
                {
                    "error":
                    "Aucune organisation associée à votre compte"
                },
                status=status.HTTP_404_NOT_FOUND
            )



        # Modification autorisée uniquement
        # pour le propriétaire.
        if request.method in [
            'PATCH',
            'PUT'
        ]:


            if user.role != "proprietaire":

                return Response(
                    {
                        "error":
                        "Seul le propriétaire peut modifier l'organisation"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )



            serializer = OrganisationSerializer(
                organisation,
                data=request.data,
                partial=True
            )


            serializer.is_valid(
                raise_exception=True
            )


            serializer.save()


            return Response(
                serializer.data
            )



        # Consultation détaillée.
        serializer = OrganisationCompleteSerializer(
            organisation
        )


        return Response(
            serializer.data
        )






    # =========================================================================
    # STATISTIQUES ORGANISATION
    # =========================================================================

    @action(
        detail=False,
        methods=['get']
    )
    def stats(self, request):
        """
        Retourne les statistiques principales
        d'une organisation.

        Exemple :
            - nombre d'événements
            - nombre de gestionnaires
            - nombre d'inscriptions
        """


        user = request.user



        # Recherche de l'organisation
        # selon le rôle utilisateur.
        if user.role == "proprietaire":

            org = Organisation.objects.filter(
                proprietaire=user
            ).first()


        else:

            org = getattr(
                user,
                "organisation",
                None
            )



        # Si aucune organisation trouvée,
        # retourne une liste vide.
        if not org:

            return Response([])



        # Retourne les statistiques.
        return Response(
            [

                {
                    "label": "Événements",
                    "value": 0,
                    "color": "blue"
                },


                {
                    "label": "Gestionnaires",

                    # Utilisation de la relation inverse
                    # pour récupérer les gestionnaires
                    # liés à l'organisation.
                    "value":
                    org.utilisateurs.filter(
                        role='gestionnaire'
                    ).count()
                    if hasattr(
                        org,
                        'utilisateurs'
                    )
                    else 0,

                    "color": "green"
                },


                {
                    "label": "Inscriptions",
                    "value": 0,
                    "color": "purple"
                }

            ]
        )