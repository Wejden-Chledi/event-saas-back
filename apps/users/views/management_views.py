# apps/users/views/management_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from apps.users.models import Utilisateur
from apps.users.serializers import UserSerializer, GestionnaireCreateSerializer, StaffCreateSerializer
from apps.users.permissions import IsProprietaire, IsGestionnaire
from apps.events.models import Evenement, AssignationEvenement
from apps.events.serializers import AssignationEvenementSerializer

class BaseUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Sécurité : on ne voit QUE les membres de SON organisation
        if not self.request.user.organisation:
            return Utilisateur.objects.none()
        return Utilisateur.objects.filter(organisation=self.request.user.organisation)

    def get_serializer_context(self):
        """Injecte l'organisation dans le contexte pour le serializer"""
        context = super().get_serializer_context()
        context["organisation"] = self.request.user.organisation
        return context

    def perform_create(self, serializer):
        # On passe l'organisation au save pour qu'elle soit dans validated_data
        serializer.save(organisation=self.request.user.organisation)

class GestionnaireViewSet(BaseUserViewSet):
    permission_classes = [IsAuthenticated, IsProprietaire]
    
    def get_queryset(self):
        return super().get_queryset().filter(role="gestionnaire")

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GestionnaireCreateSerializer
        return UserSerializer


class StaffViewSet(BaseUserViewSet):
    permission_classes = [IsAuthenticated, IsGestionnaire]

    def get_queryset(self):
        return super().get_queryset().filter(role="staff")

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffCreateSerializer
        return UserSerializer

    # --- NOUVELLE ACTION D'ASSIGNATION ---
    @action(detail=True, methods=['post'], url_path='assign_event')
    def assign_event(self, request, pk=None):
        """Route: POST /api/staff/{id}/assign_event/"""
        staff_member = self.get_object()
        event_id = request.data.get('event_id')

        if not event_id:
            return Response(
                {"error": "L'identifiant de l'événement (event_id) est requis."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # On vérifie que l'événement appartient bien à la même organisation que le gestionnaire
            evenement = Evenement.objects.get(
                id=event_id, 
                organisation=self.request.user.organisation
            )
            
            # Création de l'assignation (get_or_create évite les doublons)
            assignation, created = AssignationEvenement.objects.get_or_create(
                staff=staff_member,
                evenement=evenement
            )

            serializer = AssignationEvenementSerializer(assignation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Evenement.DoesNotExist:
            return Response(
                {"error": "Événement introuvable ou hors de votre organisation."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )