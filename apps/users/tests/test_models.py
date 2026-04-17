# apps/users/tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

# Récupération du modèle utilisateur personnalisé
Utilisateur = get_user_model()

class UtilisateurModelTest(TestCase):

    def setUp(self):
        """
        Configuration initiale pour les tests.
        Crée un utilisateur de base pour les tests de modification.
        """
        self.user_data = {
            "email": "test@example.com",
            "nom": "Dupont",
            "prenom": "Jean",
            "password": "password123"
        }
        self.user = Utilisateur.objects.create_user(**self.user_data)

    # --- TESTS DU MANAGER ---

    def test_create_user_success(self):
        """Vérifie que la création d'un utilisateur simple fonctionne."""
        user = Utilisateur.objects.create_user(
            email="new@test.com",
            nom="Martin",
            prenom="Alice",
            password="securepassword"
        )
        self.assertEqual(user.email, "new@test.com")
        self.assertEqual(user.role, "participant")  # Rôle par défaut
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email_raises_error(self):
        """Vérifie qu'une erreur est levée si l'email est manquant."""
        with self.assertRaises(ValueError):
            Utilisateur.objects.create_user(email=None, nom="X", prenom="Y")

    def test_create_superuser(self):
        """Vérifie la création d'un superutilisateur avec les bons flags."""
        admin = Utilisateur.objects.create_superuser(
            email="admin@test.com",
            nom="Admin",
            prenom="Boss",
            password="adminpassword"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, "proprietaire")
        self.assertEqual(admin.statut, "actif")

    # --- TESTS DES CONTRAINTES ---

    def test_duplicate_email_raises_error(self):
        """Vérifie que l'on ne peut pas créer deux utilisateurs avec le même email."""
        with self.assertRaises(IntegrityError):
            Utilisateur.objects.create_user(
                email="test@example.com", # Déjà utilisé dans setUp
                nom="Autre",
                prenom="Nom",
                password="password"
            )

    # --- TESTS DES MÉTHODES ---

    def test_utilisateur_str_representation(self):
        """Vérifie que la méthode __str__ renvoie le bon format."""
        expected_str = f"{self.user.nom} {self.user.prenom} ({self.user.email})"
        self.assertEqual(str(self.user), expected_str)

    def test_modifier_profil_method(self):
        """Vérifie que la méthode personnalisée modifierProfil met bien à jour les champs."""
        nouvelles_infos = {
            "nom": "Durand",
            "ville": "Paris",
            "telephone": "0123456789"
        }
        self.user.modifierProfil(**nouvelles_infos)
        
        # On rafraîchit l'instance depuis la base de données
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.nom, "Durand")
        self.assertEqual(self.user.ville, "Paris")
        self.assertEqual(self.user.telephone, "0123456789")

    # --- TESTS DE LOGIQUE DE RÔLE ---

    def test_role_choices_validation(self):
        """Vérifie que l'objet accepte les rôles définis."""
        self.user.role = "gestionnaire"
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "gestionnaire")