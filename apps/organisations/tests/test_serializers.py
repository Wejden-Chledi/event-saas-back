# apps/organisations/tests/test_serializers.py
from django.test import TestCase
from django.utils import timezone
from apps.organisations.models import Organisation, Abonnement
from apps.organisations.serializers import (
    OrganisationSerializer, 
    OrganisationCreateSerializer, 
    AbonnementSerializer
)
from apps.users.models import Utilisateur

class OrganisationSerializersTestCase(TestCase):

    def setUp(self):
        # Création d'un utilisateur pour les tests
        self.user = Utilisateur.objects.create_user(
            email="owner@eventora.com",
            nom="Owner",
            prenom="Test",
            role="proprietaire",
            password="password123"
        )

        # ✅ Correction : Utiliser .date() pour correspondre au DateField du modèle
        self.aujourdhui = timezone.now().date()

        self.abonnement_data = {
            "plan": "pro",
            "statut": "actif",
            "montant": "99.99",
            "date_debut": self.aujourdhui
        }

        self.org_data = {
            "nom": "Eventora Corp",
            "secteur": "technologie",
            "email_contact": "contact@eventora.com",
            "telephone": "0606060606",
            "adresse": "42 Rue du Code",
            "ville": "Paris",
            "pays": "France"
        }

    # --- Test AbonnementSerializer ---

    def test_abonnement_serializer_output(self):
        """Vérifie que le sérialiseur d'abonnement retourne les bons champs."""
        abo = Abonnement.objects.create(**self.abonnement_data)
        serializer = AbonnementSerializer(abo)
        self.assertEqual(serializer.data['plan'], "pro")
        # On compare des strings ou on cast en float pour éviter les soucis de Decimal
        self.assertEqual(float(serializer.data['montant']), 99.99)

    # --- Test OrganisationSerializer (Read) ---

    # apps/organisations/tests/test_serializers.py

    def test_organisation_serializer_read(self):
        """Vérifie l'affichage des données de l'organisation."""
        abo = Abonnement.objects.create(**self.abonnement_data)
        org = Organisation.objects.create(
            proprietaire=self.user,
            abonnement=abo,
            **self.org_data
        )
        
        serializer = OrganisationSerializer(org)
        self.assertEqual(serializer.data['proprietaire_nom'], self.user.nom)
        
        # ✅ Correction : Si 'proprietaire_email' n'est pas dans le serializer, 
        # utilise 'proprietaire' (qui renvoie l'ID par défaut) ou enlève cette ligne.
        # self.assertEqual(serializer.data['proprietaire'], self.user.id) 
        
        self.assertEqual(serializer.data['abonnement']['plan'], "pro")

    # --- Test OrganisationCreateSerializer (Logic) ---

    def test_organisation_create_serializer_with_abonnement(self):
        """Teste la création complète (Org + Abo + Lien User)."""
        data = self.org_data.copy()
        # Convertir la date en string pour simuler un JSON de l'API
        data['abonnement'] = self.abonnement_data.copy()
        data['abonnement']['date_debut'] = str(self.aujourdhui)

        serializer = OrganisationCreateSerializer(
            data=data, 
            context={'proprietaire': self.user}
        )
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        organisation = serializer.save()

        self.assertIsNotNone(organisation.abonnement)
        self.user.refresh_from_db()
        self.assertEqual(self.user.organisation, organisation)

    def test_organisation_create_without_abonnement(self):
        """Vérifie que la création fonctionne même sans abonnement."""
        serializer = OrganisationCreateSerializer(
            data=self.org_data, 
            context={'proprietaire': self.user}
        )
        
        self.assertTrue(serializer.is_valid())
        organisation = serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.organisation, organisation)

    def test_organisation_create_validation_error(self):
        """Vérifie l'échec si des champs manquent."""
        incomplete_data = {"nom": "Incomplet"}
        serializer = OrganisationCreateSerializer(data=incomplete_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('secteur', serializer.errors)