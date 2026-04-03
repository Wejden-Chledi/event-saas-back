# apps/events/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.users.permissions import IsGestionnaire
from .models import Evenement
from .serializers import EvenementSerializer
from .data_prep_service import EventDataPreparer
from .ai_service import generate_event_description

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from apps.users.permissions import IsStaff




class EvenementViewSet(viewsets.ModelViewSet):
    queryset = Evenement.objects.all()
    serializer_class = EvenementSerializer
    

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsGestionnaire()]


    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Evenement.objects.filter(statut="publie")
        if user.role == "gestionnaire" and hasattr(user, 'organisation'):
            return Evenement.objects.filter(organisation=user.organisation)
        return Evenement.objects.filter(statut="publie")

    def perform_create(self, serializer):
        serializer.save(
            createur=self.request.user,
            organisation=getattr(self.request.user, 'organisation', None)
        )

    # -------------------
    # IA : génération description
    # -------------------
    @action(detail=False, methods=['post'], url_path='generate-ai-desc')
    def generate_ai_desc(self, request):
        data = request.data
        preparer = EventDataPreparer()

        # Préparer tous les champs pour l'IA
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
            # Générer le prompt structuré
            prompt_text = preparer.build_structured_prompt(event_data)
            # Appel à Azure IA
            description = generate_event_description(prompt_text)
            return Response({"description": description}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class StaffAssignedEventsView(generics.ListAPIView):
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