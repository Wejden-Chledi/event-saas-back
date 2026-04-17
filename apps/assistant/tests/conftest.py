import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.events.models import Evenement

User = get_user_model()

@pytest.fixture
def test_user(db):
    """Fixture pour créer un utilisateur réutilisable."""
    return User.objects.create_user(
        email="dev@eventora.com",
        nom="Coder",
        prenom="SaaS",
        password="password123"
    )

@pytest.fixture
def test_org(test_user):
    """Fixture pour créer l'organisation obligatoire."""
    OrganisationModel = Evenement._meta.get_field('organisation').remote_field.model
    return OrganisationModel.objects.create(
        nom="Eventora Corp",
        proprietaire=test_user
    )

@pytest.fixture
def create_event(test_user, test_org):
    """Fonction pour créer rapidement des événements variés."""
    def _make_event(titre, lieu="Paris"):
        return Evenement.objects.create(
            titre=titre,
            lieu=lieu,
            date_debut=timezone.now(),
            date_fin=timezone.now() + timezone.timedelta(hours=2),
            createur=test_user,
            organisation=test_org,
            capacite_max=50
        )
    return _make_event