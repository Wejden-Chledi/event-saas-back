# apps/feedback/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from .models import Feedback, RapportIAEvenement, RapportGlobalOrganisation
from .serializers import FeedbackSerializer, RapportIASerializer
from .services import generer_rapport_ia_evenement, generer_analyse_globale_organisation

class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['proprietaire', 'gestionnaire']:
            return Feedback.objects.filter(evenement__organisation=user.organisation)
        return Feedback.objects.filter(participant=user)

    @action(detail=False, methods=['get'])
    def a_noter(self, request):
        from apps.inscriptions.models import Inscription
        from apps.events.models import Evenement

        evenements_participes_ids = Inscription.objects.filter(
            participant=request.user,
            statut='utilise'
        ).values_list('evenement_id', flat=True)

        deja_notes_ids = Feedback.objects.filter(
            participant=request.user
        ).values_list('evenement_id', flat=True)

        maintenant = timezone.now()
        events = Evenement.objects.filter(
            id__in=evenements_participes_ids
        ).exclude(
            id__in=deja_notes_ids
        ).filter(
            Q(statut='termine') | Q(date_fin__lt=maintenant)
        )

        return Response({
            "results": [
                {"id": e.id, "titre": e.titre, "date_fin": e.date_fin} for e in events
            ]
        })

    @action(detail=False, methods=['get'])
    def analyse_globale(self, request):
        """Récupère l'analyse stratégique de TOUTE l'organisation."""
        org = request.user.organisation
        if not org:
            return Response({"error": "Organisation introuvable"}, status=400)
            
        # On peut forcer le refresh avec ?refresh=true
        refresh = request.query_params.get('refresh') == 'true'
        
        if refresh:
            analyse = generer_analyse_globale_organisation(org)
        else:
            rapport = RapportGlobalOrganisation.objects.filter(organisation=org).first()
            analyse = rapport.analyse_strategique if rapport else generer_analyse_globale_organisation(org)
            
        return Response({"analyse_strategique": analyse})

class RapportIAViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RapportIAEvenement.objects.all()
    serializer_class = RapportIASerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def generer(self, request, pk=None):
        from apps.events.models import Evenement
        try:
            evenement = Evenement.objects.get(pk=pk)

            if evenement.organisation != request.user.organisation:
                return Response({"error": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

            # Le service retourne maintenant un objet RapportIAEvenement avec aide_decision
            rapport_obj = generer_rapport_ia_evenement(evenement)

            return Response({
                "analyse": rapport_obj.resume_ia,
                "decision": rapport_obj.aide_decision
            }, status=status.HTTP_200_OK)

        except Evenement.DoesNotExist:
            return Response({"error": "Événement introuvable"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)