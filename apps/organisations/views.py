from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Organisation, Abonnement
from .serializers import OrganisationSerializer, OrganisationCreateSerializer, AbonnementSerializer
from apps.users.permissions import IsAdmin


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission pour vérifier si l'utilisateur est le propriétaire ou un admin"""
    def has_object_permission(self, request, view, obj):
        return obj.proprietaire == request.user or request.user.role == "admin"


class OrganisationViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des organisations"""
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organisation.objects.all()  # Ajout du queryset
    
    def get_queryset(self):
        user = self.request.user
        # Les propriétaires voient toutes les organisations, les autres voient seulement la leur
        if user.role == "admin":
            return Organisation.objects.all()
        return Organisation.objects.filter(proprietaire=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrganisationCreateSerializer
        return OrganisationSerializer
    
    def perform_create(self, serializer):
        serializer.save(proprietaire=self.request.user)
    
    @action(detail=True, methods=['post'])
    def gerer(self, request, pk=None):
        """Gérer l'organisation (vérifier abonnement)"""
        organisation = self.get_object()
        organisation.GererOrganisation()
        return Response({'message': 'Organisation gérée avec succès', 'statut': organisation.statutAbonnement})
    
    @action(detail=True, methods=['post'])
    def renouveler_abonnement(self, request, pk=None):
        """Renouveler l'abonnement de l'organisation"""
        organisation = self.get_object()
        if not organisation.abonnement:
            return Response({'error': 'Aucun abonnement trouvé'}, status=status.HTTP_400_BAD_REQUEST)
        
        mois = request.data.get('mois', 1)
        organisation.abonnement.renouveler(mois)
        return Response({'message': f'Abonnement renouvelé pour {mois} mois'})


class AbonnementViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des abonnements"""
    serializer_class = AbonnementSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = Abonnement.objects.all()  # Ajout du queryset
    
    def get_queryset(self):
        return Abonnement.objects.all()
    
    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        """Suspendre un abonnement"""
        abonnement = self.get_object()
        abonnement.suspendre()
        return Response({'message': 'Abonnement suspendu'})
    
    @action(detail=True, methods=['post'])
    def renouveler(self, request, pk=None):
        """Renouveler un abonnement"""
        abonnement = self.get_object()
        mois = request.data.get('mois', 1)
        abonnement.renouveler(mois)
        return Response({'message': f'Abonnement renouvelé pour {mois} mois'})

