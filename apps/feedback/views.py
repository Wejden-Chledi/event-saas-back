# ============================================================================
# Fichier : apps/feedback/views.py
#
# Ce fichier contient les vues liées à la gestion des feedbacks et des analyses
# générées par l'intelligence artificielle.
#
# Il définit :
#
#   - FeedbackViewSet :
#       Gestion des avis participants, consultation des feedbacks selon le rôle
#       utilisateur et génération d'analyses globales d'organisation.
#
#   - RapportIAViewSet :
#       Consultation et génération des rapports IA associés aux événements.
#
# Ce module permet :
#   - La gestion des retours participants après participation réelle.
#   - La séparation des accès selon les rôles (participant, gestionnaire,
#     propriétaire).
#   - L'analyse automatique des feedbacks avec l'intelligence artificielle.
# ============================================================================


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from .models import Feedback, RapportIAEvenement, RapportGlobalOrganisation
from .serializers import FeedbackSerializer, RapportIASerializer
from .services import (
    generer_rapport_ia_evenement,
    generer_analyse_globale_organisation
)


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet permettant la gestion des feedbacks participants
    et des analyses globales d'une organisation.
    """

    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        """
        Retourne les feedbacks accessibles selon le rôle :

        - Propriétaire/Gestionnaire :
          accès aux feedbacks des événements de leur organisation.

        - Participant :
          accès uniquement à ses propres avis.
        """

        user = self.request.user
        org = getattr(user, 'organisation', None)


        # Les responsables d'organisation consultent les avis reçus
        if user.role in ['proprietaire', 'gestionnaire'] and org:
            return Feedback.objects.filter(
                evenement__organisation=org
            )


        # Les participants consultent uniquement leurs feedbacks
        return Feedback.objects.filter(
            participant=user
        )


    @action(detail=False, methods=['get'])
    def a_noter(self, request):
        """
        Retourne les événements terminés auxquels le participant
        a assisté mais pour lesquels aucun feedback n'a encore été donné.
        """

        from apps.inscriptions.models import Inscription
        from apps.events.models import Evenement


        # Récupération des événements où le billet a été validé
        evenements_participes_ids = Inscription.objects.filter(
            participant=request.user,
            statut='utilise'
        ).values_list(
            'evenement_id',
            flat=True
        )


        # Récupération des événements déjà évalués
        deja_notes_ids = Feedback.objects.filter(
            participant=request.user
        ).values_list(
            'evenement_id',
            flat=True
        )


        # Sélection des événements terminés non encore évalués
        maintenant = timezone.now()

        events = Evenement.objects.filter(
            id__in=evenements_participes_ids
        ).exclude(
            id__in=deja_notes_ids
        ).filter(
            Q(statut='termine') |
            Q(date_fin__lt=maintenant)
        )


        return Response({
            "results": [
                {
                    "id": e.id,
                    "titre": e.titre,
                    "date_fin": e.date_fin
                }
                for e in events
            ]
        })


    @action(detail=False, methods=['get'])
    def analyse_globale(self, request):
        """
        Retourne l'analyse stratégique IA globale
        d'une organisation.

        Le rapport peut être :
        - récupéré depuis la base de données ;
        - régénéré via le service IA.
        """

        org = getattr(request.user, 'organisation', None)


        if not org:
            return Response(
                {"error": "Organisation introuvable"},
                status=status.HTTP_400_BAD_REQUEST
            )


        # Permet de forcer une nouvelle génération IA
        refresh = request.query_params.get('refresh') == 'true'


        try:

            if refresh:
                analyse = generer_analyse_globale_organisation(org)

            else:
                # Utilisation du rapport existant s'il est disponible
                rapport = RapportGlobalOrganisation.objects.filter(
                    organisation=org
                ).first()

                if rapport and rapport.analyse_strategique:
                    analyse = rapport.analyse_strategique

                else:
                    analyse = generer_analyse_globale_organisation(org)


            return Response({
                "analyse_strategique": analyse
            })


        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class RapportIAViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule permettant de consulter
    et générer les rapports IA par événement.
    """

    queryset = RapportIAEvenement.objects.all()
    serializer_class = RapportIASerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        """
        Isolation des données :
        un gestionnaire ne peut consulter que les rapports
        liés à son organisation.
        """

        user = self.request.user
        org = getattr(user, 'organisation', None)


        if org:
            return RapportIAEvenement.objects.filter(
                evenement__organisation=org
            )


        return RapportIAEvenement.objects.none()



    @action(detail=True, methods=['post'])
    def generer(self, request, pk=None):
        """
        Génère un rapport IA pour un événement donné.
        """

        from apps.events.models import Evenement


        try:

            evenement = Evenement.objects.get(pk=pk)


            # Vérification de l'appartenance à l'organisation
            if evenement.organisation != getattr(
                request.user,
                'organisation',
                None
            ):
                return Response(
                    {"error": "Non autorisé"},
                    status=status.HTTP_403_FORBIDDEN
                )


            # Génération du rapport via le service IA
            result = generer_rapport_ia_evenement(evenement)


            # Gestion des erreurs retournées par le service
            if isinstance(result, str):
                return Response(
                    {"error": result},
                    status=status.HTTP_400_BAD_REQUEST
                )


            # Retour du rapport généré
            return Response(
                {
                    "id": result.id,
                    "resume_ia": result.resume_ia,
                    "aide_decision": result.aide_decision,
                    "evenement": evenement.id
                },
                status=status.HTTP_200_OK
            )


        except Evenement.DoesNotExist:
            return Response(
                {"error": "Événement introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )


        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )