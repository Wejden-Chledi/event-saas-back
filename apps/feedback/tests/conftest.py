import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.events.models import Evenement
from apps.inscriptions.models import Inscription
from apps.organisations.models import Organisation

User = get_user_model()

@pytest.fixture
def create_user(db):
    """Fixture pour créer un utilisateur avec les champs obligatoires."""
    def _make_user(**kwargs):
        email = kwargs.get('email', 'testuser@example.com')
        kwargs.setdefault('nom', 'NomTest')
        kwargs.setdefault('prenom', 'PrenomTest')
        
        user, created = User.objects.get_or_create(
            email=email, 
            defaults=kwargs
        )
        if created:
            user.set_password(kwargs.get('password', 'password123'))
            user.save()
        return user
    return _make_user

@pytest.fixture
def create_event(db, create_user):
    """Fixture pour créer un événement avec toutes ses contraintes (Org, Propriétaire, Créateur)."""
    def _make_event(titre, **kwargs):
        # 1. Créer un admin qui servira de propriétaire ET de créateur
        admin = create_user(email="admin.org@test.com", nom="Admin", prenom="Org")
        
        # 2. Créer ou récupérer l'organisation
        org, _ = Organisation.objects.get_or_create(
            nom="Org Test", 
            defaults={'proprietaire': admin}
        )
        
        # 3. Définir tous les champs NOT NULL identifiés
        kwargs.setdefault('createur', admin) # Correction pour l'erreur actuelle
        kwargs.setdefault('capacite_max', 100)
        kwargs.setdefault('prix', 0)
        kwargs.setdefault('description', "Description de test automatique")
        kwargs.setdefault('lieu', "Lieu de test")
        
        return Evenement.objects.create(
            titre=titre, 
            organisation=org, 
            **kwargs
        )
    return _make_event

@pytest.fixture
def auth_client():
    """Fixture pour un client API authentifié."""
    def _auth_client(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    return _auth_client

@pytest.fixture
def create_feedback_data(create_user, create_event):
    """Prépare un environnement complet : User + Event + Inscription validée."""
    def _setup():
        user = create_user(email="participant@test.com", nom="Avis", prenom="User")
        event = create_event("Event Test")
        
        # Inscription nécessaire pour valider le droit de laisser un feedback
        Inscription.objects.create(
            participant=user, 
            evenement=event, 
            statut='utilise'
        )
        return user, event
    return _setup