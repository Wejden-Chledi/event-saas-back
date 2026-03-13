from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import InformationOrganisation, Gestionnaire, DemandeAbonnement
from .serializers import (
    InformationOrganisationSerializer, 
    GestionnaireSerializer, 
    GestionnaireCreateSerializer,
    DemandeAbonnementSerializer,
    OrganisationCompleteSerializer,
    ChangerAbonnementSerializer
)
from apps.organisations.models import Organisation, Abonnement



class IsProprietaireOrReadOnly(permissions.BasePermission):
    """Permission pour vérifier si l'utilisateur est propriétaire de l'organisation"""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organisation'):
            return obj.organisation.proprietaire == request.user
        return obj.proprietaire == request.user


class InformationOrganisationViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les informations supplémentaires de l'organisation"""
    serializer_class = InformationOrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return InformationOrganisation.objects.filter(organisation__proprietaire=self.request.user)
    
    def perform_create(self, serializer):
        # Récupérer l'organisation du propriétaire
        organisation = get_object_or_404(Organisation, proprietaire=self.request.user)
        serializer.save(organisation=organisation)


class GestionnaireViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les gestionnaires de l'organisation"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Gestionnaire.objects.filter(organisation__proprietaire=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GestionnaireCreateSerializer
        return GestionnaireSerializer
    
    def perform_create(self, serializer):
        # Récupérer l'organisation du propriétaire
        organisation = get_object_or_404(Organisation, proprietaire=self.request.user)
        serializer.save(organisation=organisation)
    
    @action(detail=True, methods=['post'])
    def activer_desactiver(self, request, pk=None):
        """Activer ou désactiver un gestionnaire"""
        gestionnaire = self.get_object()
        gestionnaire.actif = not gestionnaire.actif
        gestionnaire.save()
        
        statut = "activé" if gestionnaire.actif else "désactivé"
        return Response({
            'message': f'Gestionnaire {statut} avec succès',
            'actif': gestionnaire.actif
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mon_organisation_complete(request):
    """Récupérer toutes les informations de l'organisation du propriétaire ou du gestionnaire"""
    try:
        # Si l'utilisateur est un gestionnaire
        if hasattr(request.user, 'gestionnaire_profile'):
            organisation = request.user.gestionnaire_profile.organisation
        else:
            # Sinon, c'est le propriétaire
            organisation = Organisation.objects.get(proprietaire=request.user)

        serializer = OrganisationCompleteSerializer(organisation)
        return Response(serializer.data)

    except Organisation.DoesNotExist:
        return Response(
            {'error': 'Aucune organisation trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def modifier_organisation_base(request):
    """Modifier les informations de base de l'organisation"""
    try:
        organisation = get_object_or_404(Organisation, proprietaire=request.user)
        
        # Champs modifiables
        champs_modifiables = ['nom', 'secteur', 'emailContact', 'telephone', 'adresse', 'siteWeb']
        
        for champ in champs_modifiables:
            if champ in request.data:
                setattr(organisation, champ, request.data[champ])
        
        organisation.save()
        
        return Response({
            'message': 'Informations de base modifiées avec succès',
            'organisation': {
                'id': organisation.id,
                'nom': organisation.nom,
                'secteur': organisation.secteur,
                'emailContact': organisation.emailContact,
                'telephone': organisation.telephone,
                'adresse': organisation.adresse,
                'siteWeb': organisation.siteWeb
            }
        })
    except Organisation.DoesNotExist:
        return Response(
            {'error': 'Aucune organisation trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def changer_abonnement(request):
    """Demander un changement d'abonnement"""
    try:
        organisation = get_object_or_404(Organisation, proprietaire=request.user)
        
        serializer = ChangerAbonnementSerializer(data=request.data)
        if serializer.is_valid():
            # Vérifier si une demande similaire existe déjà
            demande_existante = DemandeAbonnement.objects.filter(
                organisation=organisation,
                statut='en_attente'
            ).first()
            
            if demande_existante:
                return Response(
                    {'error': 'Une demande de changement d\'abonnement est déjà en cours'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer la nouvelle demande
            demande = DemandeAbonnement.objects.create(
                organisation=organisation,
                type_demande=serializer.validated_data['type'],
                montant_propose=serializer.validated_data['montant_propose'],
                raison=serializer.validated_data['raison']
            )
            
            return Response({
                'message': 'Demande de changement d\'abonnement envoyée avec succès',
                'demande': DemandeAbonnementSerializer(demande).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Organisation.DoesNotExist:
        return Response(
            {'error': 'Aucune organisation trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mes_demandes_abonnement(request):
    """Voir l'historique des demandes d'abonnement"""
    try:
        organisation = get_object_or_404(Organisation, proprietaire=request.user)
        demandes = DemandeAbonnement.objects.filter(organisation=organisation)
        serializer = DemandeAbonnementSerializer(demandes, many=True)
        return Response(serializer.data)
    except Organisation.DoesNotExist:
        return Response(
            {'error': 'Aucune organisation trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
