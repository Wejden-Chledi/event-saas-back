# apps/events/tests/test_models.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.users.models import Utilisateur
from apps.organisations.models import Organisation
from apps.events.models import Evenement, AssignationEvenement
from django.core.exceptions import ValidationError
from django.db import IntegrityError

class EvenementModelTestCase(TestCase):

    def setUp(self):
        # 1. Création de l'infrastructure de base
        self.proprietaire = Utilisateur.objects.create_user(
            email="owner@eventora.com",
            nom="Owner",
            prenom="Test",
            role="proprietaire",
            password="password123"
        )
        
        self.org = Organisation.objects.create(
            nom="Tech Events Org",
            secteur="technologie",
            email_contact="tech@test.com",
            proprietaire=self.proprietaire
        )

        self.event_data = {
            "titre": "Conférence IA 2026",
            "description": "Une conférence sur le futur de l'IA.",
            "lieu": "Paris",
            "capacite_max": 100,
            "prix": 50.00,
            "organisation": self.org,
            "createur": self.proprietaire,
            "date_debut": timezone.now() + timedelta(days=1),
            "date_fin": timezone.now() + timedelta(days=1, hours=4)
        }

    def test_create_evenement(self):
        """Vérifie la création simple d'un événement et son statut par défaut."""
        event = Evenement.objects.create(**self.event_data)
        self.assertEqual(event.titre, "Conférence IA 2026")
        self.assertEqual(event.statut, "brouillon")
        self.assertEqual(str(event), "Conférence IA 2026")

    def test_publier_et_annuler(self):
        """Vérifie les méthodes de changement de statut."""
        event = Evenement.objects.create(**self.event_data)
        
        event.publier()
        self.assertEqual(event.statut, "publie")
        
        event.annuler()
        self.assertEqual(event.statut, "annule")

    def test_est_termine_property(self):
        """Vérifie si la propriété est_termine détecte bien les événements passés."""
        event = Evenement.objects.create(**self.event_data)
        
        # Cas 1: Événement futur
        self.assertFalse(event.est_termine)
        
        # Cas 2: Événement passé
        event.date_fin = timezone.now() - timedelta(days=1)
        event.save()
        self.assertTrue(event.est_termine)

    def test_get_statut_reel(self):
        """Vérifie que le statut réel bascule sur 'termine' si la date est passée."""
        event = Evenement.objects.create(**self.event_data)
        event.publier()
        
        # Encore dans le futur
        self.assertEqual(event.get_statut_reel(), "publie")
        
        # Passé
        event.date_fin = timezone.now() - timedelta(hours=1)
        event.save()
        self.assertEqual(event.get_statut_reel(), "termine")

    def test_places_disponibles_initiales(self):
        """Vérifie que par défaut toutes les places sont libres."""
        event = Evenement.objects.create(**self.event_data)
        self.assertEqual(event.places_disponibles(), 100)
        self.assertFalse(event.est_complet())

    # Note: Pour tester places_disponibles avec des inscriptions, 
    # il faudra le faire une fois que l'app inscriptions sera prête.


class AssignationEvenementTestCase(TestCase):

    def setUp(self):
        self.user_owner = Utilisateur.objects.create_user(
            email="owner@test.com", nom="Owner", prenom="Test", role="proprietaire", password="pass"
        )
        self.org = Organisation.objects.create(nom="Org", proprietaire=self.user_owner)
        
        self.event = Evenement.objects.create(
            titre="Event Test", lieu="Lyon", capacite_max=10, 
            organisation=self.org, createur=self.user_owner
        )
        
        self.staff_user = Utilisateur.objects.create_user(
            email="staff@test.com", nom="Staff", prenom="User", role="staff", password="pass"
        )

    def test_assignation_staff_success(self):
        """Vérifie qu'on peut assigner un membre du staff à un événement."""
        assignation = AssignationEvenement.objects.create(
            staff=self.staff_user,
            evenement=self.event
        )
        self.assertIn(f"{self.staff_user}", str(assignation))

    def test_unique_together_assignation(self):
        """Vérifie qu'on ne peut pas assigner deux fois le même staff au même événement."""
        AssignationEvenement.objects.create(staff=self.staff_user, evenement=self.event)
        
        with self.assertRaises(IntegrityError):
            AssignationEvenement.objects.create(staff=self.staff_user, evenement=self.event)

    def test_staff_role_constraint(self):
        """
        Note: Le limit_choices_to dans Django n'empêche pas la création via Python,
        il filtre seulement dans l'admin. Pour une vraie sécurité, on peut ajouter 
        une validation personnalisée ici ou dans le clean().
        """
        pass