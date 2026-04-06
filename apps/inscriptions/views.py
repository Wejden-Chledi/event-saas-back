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

from drf_spectacular.utils import extend_schema

# Imports ReportLab pour le PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from .models import Inscription, Billet
from .serializers import InscriptionSerializer, InscriptionCreateSerializer, BilletSerializer
from .serializers import CheckInSerializer
from apps.users.permissions import IsStaff, IsGestionnaire
from apps.events.models import AssignationEvenement
from django.core.exceptions import ValidationError 

from rest_framework.permissions import IsAuthenticated
from .models import Inscription
from .serializers import ParticipantDashboardSerializer

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
    serializer_class = CheckInSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=CheckInSerializer)
    def post(self, request):
        # 1. Utilise le sérialiseur pour valider l'entrée (ID format UUID)
        serializer = CheckInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        billet_id = serializer.validated_data.get("billet_id")

        try:
            # 2. Récupération du billet avec jointures pour optimiser
            billet = Billet.objects.select_related(
                'inscription__evenement__organisation',
                'inscription__participant'
            ).get(id=billet_id)
            
            evenement = billet.inscription.evenement
            participant = billet.inscription.participant

            # 3. Logique de récupération du nom (Remplace get_full_name qui crash)
            def safe_get_name(user_obj):
                full_name = f"{getattr(user_obj, 'first_name', '')} {getattr(user_obj, 'last_name', '')}".strip()
                return full_name if full_name else user_obj.email

            # 4. Sécurité : Vérifier l'organisation du Staff
            user_org = getattr(request.user, 'organisation', None)
            if not user_org:
                return Response({"error": "Votre compte staff n'est rattaché à aucune organisation."}, status=403)
            
            if not evenement.organisation:
                return Response({"error": "Cet événement n'est rattaché à aucune organisation."}, status=403)

            # 5. Comparaison des organisations
            if user_org.pk != evenement.organisation.pk:
                return Response({"error": "Ce billet appartient à une autre organisation."}, status=403)

            # 6. Vérification de l'assignation du staff à l'événement
            is_assigned = AssignationEvenement.objects.filter(
                staff=request.user, 
                evenement=evenement
            ).exists()
            
            if not is_assigned:
                return Response({"error": "Vous n'êtes pas assigné au contrôle de cet événement."}, status=403)

            # 7. Vérifier si le billet est déjà utilisé
            if billet.utilise:
                return Response({
                    "error": "Alerte : Billet déjà utilisé !",
                    "participant": safe_get_name(participant),
                    "date": billet.date_scan.strftime('%H:%M') if billet.date_scan else "Inconnue"
                }, status=400)

            # 8. Validation finale (Transaction atomique)
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
                "participant": safe_get_name(participant)
            }, status=200)

        except Billet.DoesNotExist:
            return Response({"error": "QR Code invalide ou inconnu."}, status=404)
        except Exception as e:
            # Log précis pour toi dans le terminal
            import traceback
            print(f"--- ERREUR CRITIQUE --- : {str(e)}")
            traceback.print_exc()
            return Response({"error": f"Erreur technique : {type(e).__name__}"}, status=500)
        

# apps/inscriptions/views.py

class EventParticipantsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # On demande à Django : "Donne moi les inscriptions dont 
        # l'événement a été créé par l'utilisateur connecté"
        queryset = Inscription.objects.filter(
            evenement__createur=user
        ).distinct().order_by('-date_inscription')

        # Si vous voulez aussi que le staff assigné voie les participants :
        # queryset = Inscription.objects.filter(
        #     Q(evenement__createur=user) | Q(evenement__staff_assignes__staff=user)
        # ).distinct().order_by('-date_inscription')

        event_id = request.query_params.get('event_id')
        if event_id and event_id != "all":
            queryset = queryset.filter(evenement_id=event_id)

        serializer = ParticipantDashboardSerializer(queryset, many=True)
        return Response(serializer.data)
    



class StaffEventParticipantsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        # On ajoute 'billet' dans select_related pour charger les dates de scan d'un coup
        queryset = Inscription.objects.filter(
            evenement_id=event_id
        ).select_related('participant', 'billet').order_by('participant__nom', 'participant__prenom')
        
        serializer = ParticipantDashboardSerializer(queryset, many=True)
        return Response(serializer.data)