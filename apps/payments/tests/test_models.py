# apps/payments/tests/test_models.py
from django.test import TestCase
from apps.payments.models import Paiement
from decimal import Decimal

class PaiementModelTestCase(TestCase):
    def test_paiement_creation_and_reference(self):
        """Vérifie que la référence PAY-XXXX est générée automatiquement."""
        paiement = Paiement.objects.create(montant=Decimal("50.00"), mode='stripe')
        self.assertTrue(paiement.reference_transaction.startswith("PAY-"))
        self.assertEqual(paiement.statut, 'en_attente')

    def test_confirmer_paiement(self):
        """Vérifie le passage au statut confirmé."""
        paiement = Paiement.objects.create(montant=Decimal("20.00"))
        paiement.confirmer(external_id="pi_test_123")
        self.assertEqual(paiement.statut, 'confirme')
        self.assertEqual(paiement.external_id, "pi_test_123")