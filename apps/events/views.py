# apps/events/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

# Import des permissions personnalisées
from apps.users.permissions import IsGestionnaire, IsProprietaire, IsStaff
from .models import Evenement
from .serializers import EvenementSerializer
from .data_prep_service import EventDataPreparer
from .ai_service import generate_event_description

class EvenementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les événements.
    Incorpore une logique multi-tenant et une intégration IA.
    """
    queryset = Evenement.objects.all()
    serializer_class = EvenementSerializer

    def get_permissions(self):
        """
        Définit les permissions en fonction de l'action :
        - list/retrieve : ouvert à tous (public).
        - create/update/delete/IA : réservé aux Gestionnaires ou Propriétaires authentifiés.
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        
        # Utilisation de l'opérateur OR (|) pour autoriser Propriétaire OU Gestionnaire
        return [IsAuthenticated(), (IsProprietaire | IsGestionnaire)()]

    def get_queryset(self):
        """
        Filtre les événements selon le rôle et l'organisation :
        1. Anonyme : uniquement les événements publiés.
        2. Gestionnaire : ses propres créations au sein de son organisation.
        3. Propriétaire : tous les événements de son organisation.
        4. Autre (Staff/Participant) : uniquement les événements publiés.
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return Evenement.objects.filter(statut="publie")

        # Isolation multi-tenant
        if user.role == "gestionnaire":
            return Evenement.objects.filter(
                organisation=user.organisation, 
                createur=user
            )

        if user.role == "proprietaire":
            return Evenement.objects.filter(organisation=user.organisation)

        # Par défaut (Participants ou Staff non assignés ici)
        return Evenement.objects.filter(statut="publie")

    def perform_create(self, serializer):
        """Associe automatiquement le créateur et son organisation à l'événement."""
        serializer.save(
            createur=self.request.user,
            organisation=getattr(self.request.user, 'organisation', None)
        )

    # -------------------
    # Action Personnalisée : IA
    # -------------------
    @action(detail=False, methods=['post'], url_path='generate-ai-desc')
    def generate_ai_desc(self, request):
        """
        Endpoint POST pour générer une description via Azure OpenAI.
        Prépare les données via EventDataPreparer avant l'appel.
        """
        data = request.data
        preparer = EventDataPreparer()

        event_data = {
            "titre": data.get("titre", ""),
            "description": data.get("description", ""),
            "lieu": data.get("lieu", ""),
            "prix": data.get("prix", 0),
            "capacite_max": data.get("capacite_max", 0),
            "date_debut": data.get("date_debut"),
            "date_fin": data.get("date_fin"),
        }

        try:
            # Construction du prompt structuré (nettoyage + détection langue)
            prompt_text = preparer.build_structured_prompt(event_data)
            
            # Appel au service Azure OpenAI
            description = generate_event_description(prompt_text)
            
            return Response({"description": description}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la génération IA : {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StaffAssignedEventsView(generics.ListAPIView):
    """
    Vue réservée au Staff pour voir les événements auxquels ils sont assignés.
    """
    serializer_class = EvenementSerializer
    permission_classes = [IsAuthenticated, IsStaff]

    def get_queryset(self):
        user = self.request.user
        return Evenement.objects.filter(
            staff_assignes__staff=user,
            statut="publie"
        ).select_related("organisation", "createur") \
         .prefetch_related("photos") \
         .distinct()