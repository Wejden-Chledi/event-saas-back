# apps/users/tests/test_serializers.py
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.users.models import Utilisateur
from apps.organisations.models import Organisation, Abonnement
from apps.users.serializers import (
    UserSerializer, 
    ProprietaireRegisterSerializer, 
    ParticipantRegisterSerializer,
    GestionnaireCreateSerializer,
    StaffCreateSerializer
)

class UserSerializersTest(TestCase):

    def setUp(self):
        """Configuration initiale des tests."""
        self.user = Utilisateur.objects.create_user(
            email="test@example.com",
            nom="Dupont",
            prenom="Jean",
            password="password123",
            role="participant"
        )

    # --- 1. Test de UserSerializer (Lecture / Affichage) ---
    def test_user_serializer_fields(self):
        """Vérifie que les alias firstName/lastName et les champs calculés sont présents."""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        self.assertEqual(data['firstName'], self.user.prenom)
        self.assertEqual(data['lastName'], self.user.nom)
        self.assertIn('evenements_assignes', data)
        self.assertNotIn('password', data)  # Sécurité : pas de mot de passe en sortie

    # --- 2. Test de ProprietaireRegisterSerializer (Inscription complexe) ---
    def test_proprietaire_registration_success(self):
        """Vérifie la création atomique User + Orga + Abonnement."""
        data = {
            "nom": "Owner",
            "prenom": "Master",
            "email": "owner@startup.com",
            "password": "password123",
            "confirm_password": "password123",
            "nom_organisation": "Ma Super Orga",
            "secteur": "technologie",
            "email_contact": "contact@startup.com",
            "telephone_organisation": "0102030405",
            "adresse_org": "123 Rue Tech",
            "ville_org": "Paris",
            "pays_org": "France",
            "type_abonnement": "pro"
        }
        
        serializer = ProprietaireRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        user = serializer.save()

        # Vérifications de la logique métier
        self.assertEqual(user.role, "proprietaire")
        self.assertEqual(user.organisation.nom, "Ma Super Orga")
        self.assertEqual(user.organisation.abonnement.plan, "pro")
        
        # Vérification du calcul de la durée (pro = 90 jours)
        delta = user.organisation.abonnement.date_fin - user.organisation.abonnement.date_debut
        self.assertEqual(delta.days, 90)

    def test_proprietaire_password_mismatch(self):
        """Vérifie que la validation échoue si les mots de passe ne correspondent pas."""
        # On fournit toutes les données requises pour atteindre la méthode validate()
        data = {
            "nom": "Owner", "prenom": "Master", "email": "mismatch@test.com",
            "password": "password123", "confirm_password": "DIFFERENT_PASSWORD",
            "nom_organisation": "Orga", "secteur": "technologie",
            "email_contact": "contact@test.com", "telephone_organisation": "0102",
            "adresse_org": "Rue", "ville_org": "Paris", "pays_org": "France",
            "type_abonnement": "gratuit"
        }
        serializer = ProprietaireRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # DRF place les erreurs de validate() dans 'non_field_errors'
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(serializer.errors["non_field_errors"][0], "Les mots de passe ne correspondent pas.")

    # --- 3. Test de ParticipantRegisterSerializer ---
    def test_participant_registration_duplicate_email(self):
        """Vérifie le blocage d'un email déjà existant."""
        data = {
            "email": "test@example.com",  # Email déjà pris dans setUp
            "nom": "Nouveau",
            "prenom": "User",
            "password": "password123",
            "password_confirm": "password123"
        }
        serializer = ParticipantRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    # --- 4. Test de GestionnaireCreateSerializer ---
    def test_gestionnaire_create_without_org_in_context_fails(self):
        """Vérifie qu'une erreur est levée au save() si l'organisation manque."""
        data = {
            "email": "gestio@test.com",
            "nom": "Manager",
            "prenom": "G",
            "password": "password123",
            "statut": "actif"
        }
        # is_valid() passe car l'organisation n'est pas dans les champs obligatoires du Meta
        serializer = GestionnaireCreateSerializer(data=data, context={}) 
        self.assertTrue(serializer.is_valid())
        
        # La levée d'erreur se fait dans la méthode create() appelée par save()
        with self.assertRaises(ValidationError):
             serializer.save()

    # --- 5. Test de StaffCreateSerializer (Mise à jour) ---
    def test_staff_update_password_safety(self):
        """Vérifie que le mot de passe n'est pas écrasé par les étoiles du Front."""
        staff = Utilisateur.objects.create_user(
            email="staff@test.com", nom="S", prenom="T", role="staff"
        )
        old_password_hash = staff.password

        # Simulation d'un update Front sans changement de mot de passe
        data = {"nom": "NomModifie", "password": "********"}
        serializer = StaffCreateSerializer(instance=staff, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        staff.refresh_from_db()
        self.assertEqual(staff.nom, "NomModifie")
        self.assertEqual(staff.password, old_password_hash)  # Le hash ne doit pas avoir changé