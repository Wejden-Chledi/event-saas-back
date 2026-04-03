# apps/inscriptions/views.py
import io
import qrcode
import stripe
from django.conf import settings
from django.http import Http404, FileResponse
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

# Imports ReportLab pour le PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from .models import Inscription, Billet
from .serializers import InscriptionSerializer, InscriptionCreateSerializer, BilletSerializer
from apps.users.permissions import IsStaff, IsGestionnaire
from apps.events.models import AssignationEvenement

stripe.api_key = settings.STRIPE_SECRET_KEY

# =====================================================
# INSCRIPTIONS (PARTICIPANTS)
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
        return Inscription.objects.filter(participant=self.request.user)

class InscriptionCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            inscription = Inscription.objects.get(id=id, participant=request.user)
            
            # On ne peut annuler que si ce n'est pas encore "utilisé"
            if inscription.statut == "utilise":
                return Response({"detail": "Impossible d'annuler un billet déjà utilisé."}, status=400)

            # CAS 1 : Inscription PAYÉE -> REMBOURSEMENT STRIPE
            if inscription.statut == "paye":
                if inscription.paiement and inscription.paiement.external_id:
                    try:
                        stripe.Refund.create(payment_intent=inscription.paiement.external_id)
                    except stripe.error.StripeError as e:
                        return Response({"detail": f"Erreur Stripe: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                
                inscription.delete() 
                return Response({"detail": "Remboursement effectué et inscription libérée."}, status=status.HTTP_200_OK)

            # CAS 2 : EN ATTENTE ou autre -> Suppression simple
            else:
                inscription.delete()
                return Response({"detail": "Inscription annulée et supprimée."}, status=status.HTTP_200_OK)

        except Inscription.DoesNotExist:
            return Response({"detail": "Inscription non trouvée"}, status=status.HTTP_404_NOT_FOUND)

# =====================================================
# BILLETS & PDF
# =====================================================

class BilletListView(generics.ListAPIView):
    serializer_class = BilletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Billet.objects.filter(
            inscription__participant=self.request.user,
            inscription__statut__in=['paye', 'utilise']
        )

class BilletPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        # Recherche par ID de billet ou ID d'inscription
        billet = Billet.objects.filter(
            inscription__participant=request.user,
            inscription__statut__in=['paye', 'utilise']
        ).filter(Q(id=id) | Q(inscription__id=id)).first()

        if not billet:
            return Response({"detail": "Billet introuvable."}, status=status.HTTP_404_NOT_FOUND)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        
        # --- Design simple ---
        p.setFont("Helvetica-Bold", 18)
        p.drawString(100, 770, f"BILLET : {billet.inscription.evenement.titre}")
        p.setFont("Helvetica", 12)
        p.drawString(100, 740, f"Participant : {billet.inscription.participant.get_full_name()}")
        p.drawString(100, 720, f"Date : {billet.inscription.evenement.date_debut.strftime('%d/%m/%Y %H:%M')}")
        p.drawString(100, 700, f"Lieu : {billet.inscription.evenement.lieu}")

        # --- QR Code ---
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(str(billet.id)) 
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        img_qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        p.drawImage(ImageReader(qr_buffer), 225, 450, width=150, height=150)
        p.drawCentredString(300, 440, f"ID UNIQUE : {billet.id}")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"billet_{billet.id}.pdf")
    

class BilletDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        billet = Billet.objects.filter(
            Q(id=id) | Q(inscription__id=id)
        ).select_related('inscription', 'inscription__participant', 'inscription__evenement').first()

        if not billet:
            return Response({"detail": "Billet introuvable."}, status=404)

        if billet.inscription.participant != request.user:
            return Response({"detail": "Accès refusé."}, status=403)

        # IMPORTANT : Ajoute context={'request': request} ici
        serializer = BilletSerializer(billet, context={'request': request})
        return Response(serializer.data)

# =====================================================
# LOGIQUE STAFF & CHECK-IN
# =====================================================

class StaffBilletCheckInView(APIView):
    """
    Vue de validation : Seul le rôle 'staff' assigné peut scanner.
    Le gestionnaire ne peut pas valider d'entrée.
    """
    # On garde IsStaff | IsGestionnaire pour que le gestionnaire puisse 
    # potentiellement voir les stats, mais on bloque le POST (l'action de scan).
    permission_classes = [permissions.IsAuthenticated, IsStaff] 

    def post(self, request):
        billet_id = request.data.get("billet_id")
        
        try:
            billet = Billet.objects.select_related(
                'inscription__evenement', 
                'inscription__participant'
            ).get(id=billet_id)
            
            evenement = billet.inscription.evenement

            # 1. VÉRIFICATION DU RÔLE (Strictement Staff)
            if request.user.role != "staff":
                return Response({
                    "error": "Accès refusé. Seul le personnel de terrain (Staff) peut valider les entrées."
                }, status=403)

            # 2. VÉRIFICATION DE L'ASSIGNATION
            # On vérifie que ce staff précis est bien prévu pour cet événement
            is_assigned = AssignationEvenement.objects.filter(
                staff=request.user, 
                evenement=evenement
            ).exists()
            
            if not is_assigned:
                return Response({
                    "error": "Vous n'êtes pas assigné au contrôle de cet événement."
                }, status=403)

            # 3. SÉCURITÉ ORGANISATION (Pour éviter qu'un staff A scanne pour l'org B)
            if request.user.organisation != evenement.organisation:
                return Response({
                    "error": "Ce billet ne fait pas partie de votre organisation."
                }, status=403)

            # --- LOGIQUE DE VALIDATION ---
            if billet.utilise:
                return Response({
                    "error": "Alerte : Billet déjà utilisé !",
                    "participant": billet.inscription.participant.get_full_name(),
                    "date_scan": billet.date_scan.strftime('%H:%M')
                }, status=400)

            if billet.inscription.statut != 'paye':
                return Response({"error": "Erreur : Ce billet n'a pas été payé."}, status=400)

            # Validation finale
            billet.utilise = True
            billet.date_scan = timezone.now()
            billet.scanne_par = request.user
            billet.save()

            billet.inscription.statut = 'utilise'
            billet.inscription.save()

            return Response({
                "status": "success",
                "message": "Entrée validée !",
                "participant": billet.inscription.participant.get_full_name()
            }, status=200)

        except (Billet.DoesNotExist, ValueError):
            return Response({"error": "QR Code invalide."}, status=404)
class StaffEventParticipantsListView(generics.ListAPIView):
    """Liste des participants pour le staff (recherche manuelle)"""
    serializer_class = InscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaff | IsGestionnaire]

    def get_queryset(self):
        event_id = self.request.query_params.get('event_id')
        if not event_id:
            return Inscription.objects.none()
            
        # On s'assure que le staff ne voit que les inscrits de SON organisation
        return Inscription.objects.filter(
            evenement_id=event_id,
            evenement__organisation=self.request.user.organisation,
            statut__in=['paye', 'utilise']
        ).select_related('participant').order_by('participant__nom')