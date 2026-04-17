# apps/organisations/tests/test_models.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.organisations.models import Organisation, Abonnement
from apps.users.models import Utilisateur

class OrganisationModelsTestCase(TestCase):

    def setUp(self):
        # 1. Création d'un utilisateur pour être propriétaire
        self.user = Utilisateur.objects.create_user(
            email="boss@test.com",
            nom="Test",
            prenom="Boss",
            role="proprietaire",
            password="password123"
        )

        # 2. Création d'un abonnement actif
        self.abonnement_actif = Abonnement.objects.create(
            plan="pro",
            statut="actif",
            montant=140.00,
            date_debut=timezone.now().date(),
            date_fin=timezone.now().date() + timedelta(days=30)
        )

        # 3. Création de l'organisation
        self.org = Organisation.objects.create(
            nom="Tech Solutions",
            secteur="technologie",
            email_contact="contact@tech.com",
            telephone="0123456789",
            adresse="123 Rue de la Tech",
            proprietaire=self.user,
            abonnement=self.abonnement_actif
        )

    # --- TESTS ABONNEMENT ---

    def test_abonnement_creation(self):
        """Vérifie que l'abonnement est créé avec les bonnes valeurs."""
        self.assertEqual(self.abonnement_actif.plan, "pro")
        self.assertEqual(self.abonnement_actif.montant, 140.00)
        self.assertEqual(str(self.abonnement_actif), "pro - actif")

    def test_verifier_expiration_logic(self):
        """Vérifie que la méthode verifier_expiration change le statut si la date est passée."""
        # On crée un abonnement qui a expiré hier
        abo_expire = Abonnement.objects.create(
            plan="basique",
            statut="actif",
            date_fin=timezone.now().date() - timedelta(days=1)
        )
        abo_expire.verifier_expiration()
        self.assertEqual(abo_expire.statut, "expire")

    # --- TESTS ORGANISATION ---

    def test_organisation_creation(self):
        """Vérifie la création de l'organisation et son lien propriétaire."""
        self.assertEqual(self.org.nom, "Tech Solutions")
        self.assertEqual(self.org.proprietaire, self.user)
        self.assertEqual(str(self.org), "Tech Solutions")

    def test_est_active_method(self):
        """Vérifie que l'organisation est considérée comme active via son abonnement."""
        self.assertTrue(self.org.est_active())

        # Test sans abonnement
        self.org.abonnement = None
        self.org.save()
        self.assertFalse(self.org.est_active())

    def test_nombre_utilisateurs(self):
        """Vérifie le compte correct des utilisateurs rattachés."""
        # Initialement, l'utilisateur proprio n'est pas encore rattaché dans le setup (sauf si ton signal le fait)
        # On rattache manuellement 2 utilisateurs
        self.user.organisation = self.org
        self.user.save()
        
        Utilisateur.objects.create_user(
            email="staff@test.com", 
            nom="Staff", 
            prenom="User", 
            organisation=self.org,
            password="password123"
        )
        
        self.assertEqual(self.org.nombre_utilisateurs(), 2)

    def test_organisation_cascade_delete_user(self):
        """Si l'utilisateur propriétaire est supprimé, l'organisation doit l'être aussi (on_delete=CASCADE)."""
        org_id = self.org.id
        self.user.delete()
        with self.assertRaises(Organisation.DoesNotExist):
            Organisation.objects.get(id=org_id)

    def test_abonnement_set_null_on_delete(self):
        """Si l'abonnement est supprimé, l'organisation doit rester mais avec abonnement=None."""
        self.abonnement_actif.delete()
        self.org.refresh_from_db()
        self.assertIsNone(self.org.abonnement)