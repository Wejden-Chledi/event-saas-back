from django.test import TestCase
from django.utils import timezone
from apps.users.models import Utilisateur
from apps.events.models import Evenement
from apps.organisations.models import Organisation
from apps.payments.models import Paiement
from apps.inscriptions.models import Inscription, Billet
from unittest.mock import patch

class InscriptionModelTestCase(TestCase):
    def setUp(self):
        # Ajout de nom et prenom pour respecter les contraintes de ton UserManager
        self.user = Utilisateur.objects.create_user(
            email="client@test.com", 
            password="pass", 
            nom="Client", 
            prenom="Test"
        )
        self.owner = Utilisateur.objects.create_user(
            email="owner@test.com", 
            password="pass", 
            role="proprietaire",
            nom="Owner",
            prenom="Test"
        )
        self.org = Organisation.objects.create(nom="Org Test", proprietaire=self.owner)
        self.event = Evenement.objects.create(
            titre="Concert", 
            organisation=self.org, 
            createur=self.owner,
            capacite_max=100,
            prix=50.0,
            statut="publie",
            date_debut=timezone.now() + timezone.timedelta(days=1),
            date_fin=timezone.now() + timezone.timedelta(days=1, hours=2)
        )

    def test_inscription_reference_generation(self):
        """Vérifie qu'une référence unique EVT-XXXX est générée au save."""
        ins = Inscription.objects.create(participant=self.user, evenement=self.event)
        self.assertTrue(ins.reference_paiement.startswith("EVT-"))
        self.assertEqual(len(ins.reference_paiement), 14)

    def test_signal_paiement_confirme_cree_billet(self):
        """Vérifie que le signal crée un billet quand le paiement est confirmé."""
        paiement = Paiement.objects.create(montant=50.0, statut='en_attente')
        ins = Inscription.objects.create(
            participant=self.user, 
            evenement=self.event, 
            paiement=paiement
        )
        
        # Simuler la confirmation du paiement
        paiement.statut = "confirme"
        paiement.save()
        
        ins.refresh_from_db()
        self.assertEqual(ins.statut, "paye")
        self.assertTrue(Billet.objects.filter(inscription=ins).exists())

    @patch('apps.inscriptions.models.Billet.generer_qr_code')
    def test_billet_qr_generation_on_save(self, mock_gen_qr):
        """Vérifie que la méthode de génération QR est appelée au bon moment."""
        ins = Inscription.objects.create(
            participant=self.user, 
            evenement=self.event, 
            statut="paye"
        )
        billet = Billet(inscription=ins)
        billet.save()
        
        mock_gen_qr.assert_called_once()

    def test_signal_error_handling(self):
        """Vérifie que le signal ne fait pas crash le système en cas d'erreur."""
        with patch('apps.inscriptions.models.Billet.objects.get_or_create', side_effect=Exception("DB Error")):
            paiement = Paiement.objects.create(montant=10.0, statut='confirme')
            # Le test passe si aucune exception n'est levée (car le signal a un try/except)
            self.assertTrue(Paiement.objects.filter(id=paiement.id).exists())

    def test_billet_wont_regenerate_qr_if_exists(self):
        """Vérifie qu'on ne régénère pas le QR code si déjà présent."""
        ins = Inscription.objects.create(participant=self.user, evenement=self.event, statut="paye")
        billet = Billet.objects.create(inscription=ins)
        with patch.object(Billet, 'generer_qr_code') as mock_gen:
            billet.save()
            mock_gen.assert_not_called()    