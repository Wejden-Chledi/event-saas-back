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
    """
    Gestion des feedbacks participants et analyses globales pour les gestionnaires.
    """
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        org = getattr(user, 'organisation', None)
        
        # Si c'est un gestionnaire, on voit tous les feedbacks de son organisation
        if user.role in ['proprietaire', 'gestionnaire'] and org:
            return Feedback.objects.filter(evenement__organisation=org)
        
        # Si c'est un participant, il ne voit que ses propres feedbacks
        return Feedback.objects.filter(participant=user)

    @action(detail=False, methods=['get'])
    def a_noter(self, request):
        """
        Liste les événements terminés auxquels le participant a assisté 
        mais n'a pas encore donné de feedback.
        """
        from apps.inscriptions.models import Inscription
        from apps.events.models import Evenement

        # 1. Événements où le billet a été scanné (statut 'utilise')
        evenements_participes_ids = Inscription.objects.filter(
            participant=request.user,
            statut='utilise'
        ).values_list('evenement_id', flat=True)

        # 2. Événements déjà notés
        deja_notes_ids = Feedback.objects.filter(
            participant=request.user
        ).values_list('evenement_id', flat=True)

        # 3. Filtrer les événements éligibles (terminés ou date passée)
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
        """
        Récupère ou génère l'analyse stratégique IA pour l'ensemble de l'organisation.
        """
        org = getattr(request.user, 'organisation', None)
        if not org:
            return Response({"error": "Organisation introuvable"}, status=status.HTTP_400_BAD_REQUEST)
            
        refresh = request.query_params.get('refresh') == 'true'
        
        try:
            if refresh:
                analyse = generer_analyse_globale_organisation(org)
            else:
                rapport = RapportGlobalOrganisation.objects.filter(organisation=org).first()
                if rapport and rapport.analyse_strategique:
                    analyse = rapport.analyse_strategique
                else:
                    analyse = generer_analyse_globale_organisation(org)
            
            return Response({"analyse_strategique": analyse})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RapportIAViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter et générer des rapports IA par événement.
    """
    queryset = RapportIAEvenement.objects.all()
    serializer_class = RapportIASerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Sécurité : Un gestionnaire ne voit que les rapports de son organisation
        user = self.request.user
        org = getattr(user, 'organisation', None)
        if org:
            return RapportIAEvenement.objects.filter(evenement__organisation=org)
        return RapportIAEvenement.objects.none()

    @action(detail=True, methods=['post'])
    def generer(self, request, pk=None):
        """
        Déclenche l'analyse IA pour un événement spécifique.
        """
        from apps.events.models import Evenement
        try:
            evenement = Evenement.objects.get(pk=pk)

            # Vérification des droits
            if evenement.organisation != getattr(request.user, 'organisation', None):
                return Response({"error": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

            # Appel au service IA (OpenAI / Azure)
            rapport_obj = generer_rapport_ia_evenement(evenement)

            return Response({
                "id": rapport_obj.id,
                "analyse": rapport_obj.resume_ia,
                "decision": rapport_obj.aide_decision,
                "evenement": evenement.id
            }, status=status.HTTP_200_OK)

        except Evenement.DoesNotExist:
            return Response({"error": "Événement introuvable"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)