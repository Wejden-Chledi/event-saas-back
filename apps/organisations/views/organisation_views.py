# apps/organisations/views/organisation_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.permissions import IsProprietaire, IsGestionnaire
from ..models import Organisation
from ..serializers import (
    OrganisationSerializer, 
    OrganisationCompleteSerializer, 
    OrganisationCreateSerializer
)

class OrganisationViewSet(viewsets.ModelViewSet):
    """
    Gestion des organisations (Multi-tenant).
    Un propriétaire ne gère que la sienne.
    Un gestionnaire peut consulter celle à laquelle il est rattaché.
    """
    
    def get_permissions(self):
        """Gestion fine des permissions par action."""
        if self.action in ['list', 'retrieve', 'me', 'stats']:
            # Propriétaire OU Gestionnaire peuvent voir
            return [IsAuthenticated(), (IsProprietaire | IsGestionnaire)()]
        # Seul le Propriétaire peut créer ou modifier lourdement
        return [IsAuthenticated(), IsProprietaire()]

    def get_queryset(self):
        """Filtre les données pour garantir l'étanchéité entre clients (SaaS)."""
        user = self.request.user
        if not user.is_authenticated:
            return Organisation.objects.none()

        # Le propriétaire voit SA propre organisation
        if user.role == "proprietaire":
            return Organisation.objects.filter(proprietaire=user)
        
        # Le gestionnaire voit l'organisation liée à son profil
        if hasattr(user, 'organisation') and user.organisation:
            return Organisation.objects.filter(id=user.organisation.id)
            
        return Organisation.objects.none()

    def get_serializer_class(self):
        """Sélectionne le sérialiseur selon l'action."""
        if self.action == 'create':
            return OrganisationCreateSerializer
        if self.action in ['retrieve', 'me']:
            return OrganisationCompleteSerializer
        return OrganisationSerializer

    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        """
        Récupère ou modifie l'organisation de l'utilisateur connecté.
        Route : /api/organisations/me/
        """
        # Vérification de l'existence de l'organisation
        if not hasattr(request.user, 'organisation') or not request.user.organisation:
            return Response({"error": "Aucune organisation trouvée"}, status=404)
        
        organisation = request.user.organisation

        # --- LOGIQUE DE MISE À JOUR (PATCH/PUT) ---
        if request.method in ['PATCH', 'PUT']:
            # Seul le propriétaire devrait pouvoir modifier
            if request.user.role != 'proprietaire':
                return Response({"error": "Seul le propriétaire peut modifier les infos"}, status=403)
            
            serializer = OrganisationSerializer(organisation, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        # --- LOGIQUE DE LECTURE (GET) ---
        serializer = OrganisationCompleteSerializer(organisation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Données pour le dashboard.
        Route : /api/organisations/stats/
        """
        org = getattr(request.user, 'organisation', None)
        if not org:
            return Response([], status=200)
            
        # Ici, vous pourrez injecter de vrais counts plus tard
        # Ex: org.evenements.count()
        data = [
            {"label": "Événements", "value": 0, "color": "blue"},
            {"label": "Gestionnaires", "value": org.utilisateurs.filter(role='gestionnaire').count(), "color": "green"},
            {"label": "Inscriptions", "value": 0, "color": "purple"},
        ]
        return Response(data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        """Assigne automatiquement le créateur comme propriétaire."""
        serializer.save(proprietaire=self.request.user)