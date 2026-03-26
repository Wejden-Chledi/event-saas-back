# apps/inscriptions/views.py
import io
import qrcode
from django.http import Http404, FileResponse
from django.db import models
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

# Imports ReportLab pour le PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from .models import Inscription, Billet
from .serializers import InscriptionSerializer, InscriptionCreateSerializer, BilletSerializer
from apps.payments.models import Paiement
import stripe
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY

# =====================================================
# INSCRIPTIONS
# =====================================================

class InscriptionCreateView(generics.CreateAPIView):
    queryset = Inscription.objects.all()
    serializer_class = InscriptionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

class ParticipantInscriptionsListView(generics.ListAPIView):
    serializer_class = InscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Inscription.objects.filter(
            participant=self.request.user
        ).order_by('-date_inscription')

class InscriptionDetailView(generics.RetrieveAPIView):
    serializer_class = InscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        # Un utilisateur ne peut voir que ses propres inscriptions
        return Inscription.objects.filter(participant=self.request.user)



class InscriptionCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            inscription = Inscription.objects.get(id=id, participant=request.user)
            
            # CAS 1 : Inscription PAYÉE -> REMBOURSEMENT STRIPE + SUPPRESSION
            if inscription.statut == "paye":
                if inscription.paiement and inscription.paiement.external_id:
                    try:
                        # Déclencher le remboursement réel sur Stripe
                        stripe.Refund.create(payment_intent=inscription.paiement.external_id)
                    except stripe.error.StripeError as e:
                        return Response({"detail": f"Erreur Stripe: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                
                # Une fois le remboursement lancé, on supprime l'inscription 
                # pour permettre une réinscription immédiate.
                inscription.delete() 
                return Response({"detail": "Remboursement effectué et inscription libérée."}, status=status.HTTP_200_OK)

            # CAS 2 : Inscription EN ATTENTE -> SUPPRESSION SIMPLE
            else:
                # On supprime l'objet de la base de données
                # Cela réinitialise le validateur "exists()" du Serializer
                inscription.delete()
                return Response({"detail": "Inscription annulée et supprimée."}, status=status.HTTP_200_OK)

        except Inscription.DoesNotExist:
            return Response({"detail": "Inscription non trouvée"}, status=status.HTTP_404_NOT_FOUND)
# =====================================================
# BILLETS
# =====================================================

class BilletListView(generics.ListAPIView):
    serializer_class = BilletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # On ne liste que les billets dont l'inscription est payée ou utilisée
        return Billet.objects.filter(
            inscription__participant=self.request.user,
            inscription__statut__in=['paye', 'utilise']
        )

class BilletDetailView(generics.RetrieveAPIView):
    serializer_class = BilletSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Billet.objects.filter(
            inscription__participant=self.request.user,
            inscription__statut__in=['paye', 'utilise']
        )

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.filter(
            Q(id=self.kwargs['id']) | Q(inscription__id=self.kwargs['id'])
        ).first()
        
        if not obj:
            raise Http404("Billet non trouvé ou non encore disponible (paiement requis).")
        return obj

# =====================================================
# GÉNÉRATION PDF AVEC QR CODE
# =====================================================

class BilletPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        # 1. Recherche sécurisée : il faut que l'inscription soit PAYÉE pour avoir le PDF
        billet = Billet.objects.filter(
            inscription__participant=request.user,
            inscription__statut__in=['paye', 'utilise']
        ).filter(Q(id=id) | Q(inscription__id=id)).first()

        if not billet:
            return Response(
                {"detail": "Billet non trouvé ou paiement non confirmé."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Préparation du buffer PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        
        # --- Design du Billet ---
        p.setFont("Helvetica-Bold", 18)
        titre_event = billet.inscription.evenement.titre
        p.drawString(100, 770, f"BILLET OFFICIEL : {titre_event}")
        
        p.setFont("Helvetica", 12)
        nom_complet = f"{billet.inscription.participant.prenom} {billet.inscription.participant.nom}"
        p.drawString(100, 740, f"Participant : {nom_complet}")
        
        date_str = billet.inscription.evenement.date_debut.strftime('%d/%m/%Y %H:%M')
        p.drawString(100, 720, f"Date : {date_str}")
        
        lieu = getattr(billet.inscription.evenement, 'lieu', 'À confirmer')
        p.drawString(100, 700, f"Lieu : {lieu}")

        # --- GÉNÉRATION DU CODE QR ---
        # On utilise l'ID du billet pour le scan à l'entrée
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(str(billet.id)) 
        qr.make(fit=True)
        
        img_qr = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        img_qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Insertion de l'image QR dans le PDF
        p.drawImage(ImageReader(qr_buffer), 225, 450, width=150, height=150)
        
        p.setFont("Courier", 10)
        p.drawCentredString(300, 440, f"ID UNIQUE : {billet.id}")
        
        # Information de sécurité
        p.setFont("Helvetica-Oblique", 8)
        p.drawCentredString(300, 420, "Ce billet est unique. Présentez-le à l'entrée de l'événement.")
        
        # --- Finalisation ---
        p.showPage()
        p.save()

        buffer.seek(0)
        filename = f"billet_{titre_event.replace(' ', '_')}.pdf"
        return FileResponse(buffer, as_attachment=True, filename=filename)