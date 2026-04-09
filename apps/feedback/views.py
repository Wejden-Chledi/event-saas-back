# apps/feedback/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from .models import Feedback, RapportIAEvenement
from .serializers import FeedbackSerializer, RapportIASerializer
from .services import generer_rapport_ia_evenement

class FeedbackViewSet(viewsets.ModelViewSet):
    """
    Gestion des avis (Feedbacks).
    Les participants voient leurs propres avis.
    Les gestionnaires voient les avis de leur organisation.
    """
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Sécurité : filtrage selon le rôle
        if user.role in ['proprietaire', 'gestionnaire']:
            return Feedback.objects.filter(evenement__organisation=user.organisation)
        return Feedback.objects.filter(participant=user)

    @action(detail=False, methods=['get'])
    def a_noter(self, request):
        """
        Récupère la liste des événements terminés auxquels l'utilisateur 
        a participé (billet scanné) et qu'il n'a pas encore notés.
        """
        from apps.inscriptions.models import Inscription
        from apps.events.models import Evenement

        # 1. On récupère les IDs des événements où l'utilisateur a été scanné (utilise)
        evenements_participes_ids = Inscription.objects.filter(
            participant=request.user,
            statut='utilise'
        ).values_list('evenement_id', flat=True)

        # 2. On récupère les IDs des événements déjà notés par l'utilisateur
        deja_notes_ids = Feedback.objects.filter(
            participant=request.user
        ).values_list('evenement_id', flat=True)

        # 3. Filtrage final des événements :
        # - Doit être dans la liste des participés
        # - Ne doit pas être dans la liste des déjà notés
        # - Doit être soit marqué 'termine', soit avoir une date de fin passée
        maintenant = timezone.now()
        
        events = Evenement.objects.filter(
            id__in=evenements_participes_ids
        ).exclude(
            id__in=deja_notes_ids
        ).filter(
            Q(statut='termine') | Q(date_fin__lt=maintenant)
        )

        # Debug console pour le développement
        print(f"DEBUG Feedback: User={request.user.email}, Found={events.count()}")

        # 4. Formatage de la réponse pour le frontend (clé 'results')
        return Response({
            "results": [
                {
                    "id": e.id, 
                    "titre": e.titre,
                    "date_fin": e.date_fin
                } for e in events
            ]
        })

class RapportIAViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vue en lecture seule pour consulter les rapports d'analyse IA.
    """
    queryset = RapportIAEvenement.objects.all()
    serializer_class = RapportIASerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def generer(self, request, pk=None):
        """
        Action personnalisée pour déclencher l'analyse IA sur un événement.
        """
        from apps.events.models import Evenement

        try:
            evenement = Evenement.objects.get(pk=pk)

            # Vérification de sécurité : le gestionnaire doit appartenir à la même org
            if evenement.organisation != request.user.organisation:
                return Response({"error": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

            # Appel au service qui communique avec Azure OpenAI
            analyse = generer_rapport_ia_evenement(evenement)

            return Response({"rapport": analyse}, status=status.HTTP_200_OK)

        except Evenement.DoesNotExist:
            return Response({"error": "Événement introuvable"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)