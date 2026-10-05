# apps/users/views/management_views.py
#
# Ce fichier contient les ViewSets permettant la gestion des utilisateurs
# (Gestionnaires et Staff) ainsi que l'assignation du staff aux événements.
# ============================================================================


from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from apps.users.models import Utilisateur
from apps.users.serializers import (
    UserSerializer,
    GestionnaireCreateSerializer,
    StaffCreateSerializer,
)
from apps.users.permissions import (
    IsProprietaire,
    IsGestionnaire,
)
from apps.events.models import (
    Evenement,
    AssignationEvenement,
)
from apps.events.serializers import AssignationEvenementSerializer


# ============================================================================
# CLASSE DE BASE
# ============================================================================

class BaseUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet de base utilisé par GestionnaireViewSet et StaffViewSet.

    Cette classe contient les fonctionnalités communes :
        - Authentification obligatoire
        - Restriction aux utilisateurs de la même organisation
        - Injection automatique de l'organisation
        - Affectation automatique de l'organisation lors de la création
    """
    permission_classes = [IsAuthenticated]

    # ------------------------------------------------------------------------
    # Détermine les utilisateurs visibles.
    # ------------------------------------------------------------------------
    def get_queryset(self):
        """
        Retourne uniquement les utilisateurs appartenant
        à la même organisation que l'utilisateur connecté.

        Cela empêche un utilisateur d'accéder
        aux membres d'une autre organisation.
        """

        # Si l'utilisateur n'appartient à aucune organisation,
        # aucun résultat n'est retourné.
        if not self.request.user.organisation:
            return Utilisateur.objects.none()

        # Retourne uniquement les utilisateurs
        # de la même organisation.
        return Utilisateur.objects.filter(
            organisation=self.request.user.organisation
        )

    # ------------------------------------------------------------------------
    # Ajout de données supplémentaires au serializer.
    # ------------------------------------------------------------------------
    def get_serializer_context(self):
        """
        Injecte automatiquement l'organisation
        dans le contexte du serializer.

        Les serializers pourront récupérer cette valeur via :
            self.context["organisation"]
        """

        context = super().get_serializer_context()

        context["organisation"] = self.request.user.organisation

        return context

    # ------------------------------------------------------------------------
    # Création d'un utilisateur.
    # ------------------------------------------------------------------------
    def perform_create(self, serializer):
        """
        Lors de la création d'un utilisateur,
        son organisation est automatiquement renseignée.
        """

        serializer.save(
            organisation=self.request.user.organisation
        )


# ============================================================================
# GESTION DES GESTIONNAIRES
# ============================================================================

class GestionnaireViewSet(BaseUserViewSet):
    """
    ViewSet réservé au propriétaire.

    Permet :
        - lister les gestionnaires
        - créer un gestionnaire
        - modifier un gestionnaire
        - supprimer un gestionnaire
    """

    # Seul un propriétaire authentifié possède l'accès.
    permission_classes = [
        IsAuthenticated,
        IsProprietaire
    ]

    # ------------------------------------------------------------------------
    # Liste uniquement les utilisateurs ayant le rôle Gestionnaire.
    # ------------------------------------------------------------------------
    def get_queryset(self):

        return super().get_queryset().filter(
            role="gestionnaire"
        )

    # ------------------------------------------------------------------------
    # Choix dynamique du serializer.
    # ------------------------------------------------------------------------
    def get_serializer_class(self):
        """
        Lors de la création ou modification,
        on utilise un serializer spécifique.

        Pour la lecture,
        on utilise le serializer classique.
        """

        if self.action in [
            "create",
            "update",
            "partial_update",
        ]:
            return GestionnaireCreateSerializer

        return UserSerializer


# ============================================================================
# GESTION DU STAFF
# ============================================================================

class StaffViewSet(BaseUserViewSet):
    """
    ViewSet destiné aux gestionnaires.

    Il permet :

        - gérer les membres du staff
        - assigner un staff à un événement
    """

    permission_classes = [
        IsAuthenticated,
        IsGestionnaire
    ]

    # ------------------------------------------------------------------------
    # Liste des membres du staff.
    # ------------------------------------------------------------------------
    def get_queryset(self):

        user = self.request.user

        queryset = super().get_queryset().filter(
            role="staff"
        )

        # Si l'utilisateur connecté est un gestionnaire,
        # il ne peut voir que les membres du staff
        # qu'il a lui-même créés.
        if user.role == "gestionnaire":
            return queryset.filter(
                createur=user
            )

        return queryset

    # ------------------------------------------------------------------------
    # Création d'un membre du staff.
    # ------------------------------------------------------------------------
    def perform_create(self, serializer):
        """
        Lors de la création :

            - l'organisation est automatiquement affectée
            - le créateur est enregistré
        """

        serializer.save(
            organisation=self.request.user.organisation,
            createur=self.request.user
        )

    # ------------------------------------------------------------------------
    # Choix du serializer.
    # ------------------------------------------------------------------------
    def get_serializer_class(self):

        if self.action in [
            "create",
            "update",
            "partial_update",
        ]:
            return StaffCreateSerializer

        return UserSerializer


    # =========================================================================
    # ACTION PERSONNALISÉE
    # =========================================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="assign_event"
    )
    def assign_event(self, request, pk=None):
        """
        Route personnalisée :

            POST /api/staff/{id}/assign_event/

        Cette méthode permet d'affecter un membre du staff
        à un événement.
        """

        # Récupère automatiquement le membre du staff
        # correspondant à l'id de l'URL.
        staff_member = self.get_object()

        # Récupère l'identifiant de l'événement envoyé
        # dans le corps de la requête.
        event_id = request.data.get("event_id")

        # Vérifie que l'identifiant existe.
        if not event_id:

            return Response(
                {
                    "error": (
                        "L'identifiant de l'événement "
                        "(event_id) est requis."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            # Recherche l'événement uniquement
            # dans l'organisation du gestionnaire.
            evenement = Evenement.objects.get(
                id=event_id,
                organisation=self.request.user.organisation
            )

            # Création de l'assignation.
            #
            # get_or_create permet d'éviter
            # la création de doublons.
            assignation, created = (
                AssignationEvenement.objects.get_or_create(
                    staff=staff_member,
                    evenement=evenement
                )
            )

            # Sérialisation des données.
            serializer = AssignationEvenementSerializer(
                assignation
            )

            # Retourne l'assignation créée.
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        # L'événement n'existe pas.
        except Evenement.DoesNotExist:

            return Response(
                {
                    "error": (
                        "Événement introuvable "
                        "ou hors de votre organisation."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Gestion des autres erreurs.
        except Exception as e:

            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )