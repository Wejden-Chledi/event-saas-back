# apps/inscriptions/views.py
import io
import qrcode
import stripe
from django.conf import settings
from django.http import Http404, FileResponse
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
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
from django.core.exceptions import ValidationError 

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

        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            
            # --- Sécurité pour le nom ---
            participant = billet.inscription.participant
            nom_complet = f"{participant.first_name} {participant.last_name}" if hasattr(participant, 'first_name') else participant.email

            # --- Sécurité pour la date ---
            evenement = billet.inscription.evenement
            date_str = evenement.date_debut.strftime('%d/%m/%Y %H:%M') if evenement.date_debut else "Date non définie"

            # --- Design du PDF ---
            p.setFont("Helvetica-Bold", 18)
            p.drawString(100, 770, f"BILLET : {evenement.titre}")
            
            p.setFont("Helvetica", 12)
            p.drawString(100, 740, f"Participant : {nom_complet}")
            p.drawString(100, 720, f"Date : {date_str}")
            p.drawString(100, 700, f"Lieu : {evenement.lieu or 'Non spécifié'}")

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

        except Exception as e:
            # Si ça plante, on print l'erreur exacte dans les logs Azure
            print(f"ERREUR GENERATION PDF: {str(e)}")
            return Response({"detail": f"Erreur lors de la création du PDF: {str(e)}"}, status=500)

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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        billet_id = request.data.get("billet_id")
        
        if not billet_id:
            return Response({"error": "ID du billet manquant."}, status=400)

        try:
            # 1. Récupération robuste
            billet = Billet.objects.select_related(
                'inscription__evenement', 
                'inscription__participant',
                'inscription__evenement__organisation'
            ).get(id=billet_id)
            
            evenement = billet.inscription.evenement

            # 2. Vérification de l'organisation
            # Utilisation de .pk pour éviter les problèmes si l'objet n'est pas chargé
            staff_org_id = request.user.organisation.pk if request.user.organisation else None
            event_org_id = evenement.organisation.pk if evenement.organisation else None

            if staff_org_id != event_org_id or staff_org_id is None:
                return Response({
                    "error": "Ce billet ne fait pas partie de votre organisation."
                }, status=403)

            # 3. Vérification de l'assignation
            is_assigned = AssignationEvenement.objects.filter(
                staff=request.user, 
                evenement=evenement
            ).exists()
            
            if not is_assigned:
                return Response({
                    "error": "Vous n'êtes pas assigné à cet événement."
                }, status=403)

            # 4. Vérification si déjà utilisé
            if billet.utilise:
                date_str = billet.date_scan.strftime('%H:%M') if billet.date_scan else "inconnue"
                return Response({
                    "error": f"Alerte : Billet déjà utilisé à {date_str} !",
                    "participant": billet.inscription.participant.get_full_name(),
                }, status=400)

            # 5. Validation atomique (Sauvegarde sécurisée)
            with transaction.atomic():
                billet.utilise = True
                billet.date_scan = timezone.now()
                billet.scanne_par = request.user
                billet.save()

                inscription = billet.inscription
                inscription.statut = 'utilise'
                inscription.save()

            return Response({
                "status": "success",
                "message": "Entrée validée !",
                "participant": inscription.participant.get_full_name()
            }, status=200)

        except (Billet.DoesNotExist, ValidationError, ValueError):
            return Response({"error": "QR Code invalide ou billet inconnu."}, status=404)
        except Exception as e:
            # On log l'erreur pour Azure Log Stream
            print(f"--- ERREUR CRITIQUE CHECK-IN ---")
            print(f"User: {request.user.email} | Billet: {billet_id}")
            print(f"Exception: {str(e)}")
            return Response({"error": "Erreur interne du serveur."}, status=500)
        

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