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
    # ✅ Autoriser Propriétaire OU Gestionnaire
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'me', 'stats']:
            return [IsAuthenticated(), (IsProprietaire | IsGestionnaire)()]
        return [IsAuthenticated(), IsProprietaire()]

    def get_queryset(self):
        user = self.request.user
        # ✅ Le propriétaire voit l'organisation qu'il possède
        if user.role == "proprietaire":
            return Organisation.objects.filter(proprietaire=user)
        # ✅ Le gestionnaire voit l'organisation à laquelle il est rattaché
        if user.role == "gestionnaire" and hasattr(user, 'organisation_set'):
             # Si c'est une ForeignKey sur Organisation
             return Organisation.objects.filter(id=user.organisation_id)
        
        return Organisation.objects.none()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Action universelle pour récupérer SON organisation"""
        # On cherche l'organisation rattachée (selon votre modèle User)
        org = None
        if hasattr(request.user, 'organisation') and request.user.organisation:
            org = request.user.organisation
        elif hasattr(request.user, 'organisation_managed'): # exemple si le nom est différent
            org = request.user.organisation_managed
            
        if not org:
            return Response({"error": "Aucune organisation trouvée"}, status=404)
            
        serializer = OrganisationCompleteSerializer(org)
        return Response(serializer.data)
    permission_classes = [IsAuthenticated, IsProprietaire]

    def get_queryset(self):
        # Sécurité : Un propriétaire ne voit que SA propre organisation
        return Organisation.objects.filter(proprietaire=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrganisationCreateSerializer
        if self.action in ['retrieve', 'me']:
            return OrganisationCompleteSerializer
        return OrganisationSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupère l'organisation de l'utilisateur connecté : /api/organisations/me/"""
        # Utilise l'attribut organisation lié à l'utilisateur (OneToOneField)
        if not hasattr(request.user, 'organisation') or not request.user.organisation:
            return Response({"error": "Aucune organisation trouvée"}, status=404)
            
        serializer = OrganisationCompleteSerializer(request.user.organisation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Action pour les infos du dashboard : /api/organisations/stats/"""
        if not hasattr(request.user, 'organisation') or not request.user.organisation:
            return Response([], status=200) # On renvoie une liste vide au lieu d'une 404 pour le dashboard
            
        # Exemple de stats (à adapter selon vos modèles réels)
        # Note : Pensez à importer vos modèles d'événements et de gestionnaires ici
        data = [
            {"label": "Événements", "value": 0, "color": "blue"},
            {"label": "Gestionnaires", "value": 0, "color": "green"},
            {"label": "Inscriptions", "value": 0, "color": "purple"},
        ]
        return Response(data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(proprietaire=self.request.user)