import logging
import traceback
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas

from apps.events.models import Evenement, Inscription, Billet
from apps.events.serializers import InscriptionSerializer, BilletSerializer

logger = logging.getLogger(__name__)


# =============================
# Inscription à un événement
# =============================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_event_participant(request):
    try:
        user = request.user
        event_id = request.data.get("event_id")

        if not event_id:
            return Response(
                {"success": False, "message": "event_id requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        evenement = get_object_or_404(Evenement, id=event_id)

        # Vérifier si déjà inscrit
        if Inscription.objects.filter(participant=user, evenement=evenement).exists():
            return Response(
                {"success": False, "message": "Déjà inscrit à cet événement"}
            )

        # Vérifier capacité
        total = Inscription.objects.filter(evenement=evenement).count()

        if hasattr(evenement, "capacite_max") and evenement.capacite_max:
            if total >= evenement.capacite_max:
                return Response(
                    {"success": False, "message": "Plus de places disponibles"}
                )

        # Création inscription
        inscription = Inscription.objects.create(
            participant=user,
            evenement=evenement,
            statut="en_attente",
            montant_paye=getattr(evenement, "prix", 0)
        )

        inscription.generer_reference()
        inscription.save()

        # Création billet (QR code généré automatiquement dans le modèle)
        Billet.objects.create(inscription=inscription)

        serializer = InscriptionSerializer(inscription)

        return Response({
            "success": True,
            "inscription": serializer.data
        })

    except Exception as e:
        logger.error(
            f"Erreur lors de l'inscription utilisateur {user.id} à l'événement {event_id}: {e}"
        )
        logger.error(traceback.format_exc())

        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================
# Mes inscriptions (dashboard)
# =============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_inscriptions(request):
    try:
        user = request.user

        inscriptions = Inscription.objects.filter(
            participant=user
        ).select_related("evenement")

        serializer = InscriptionSerializer(inscriptions, many=True)

        return Response(serializer.data)

    except Exception as e:
        logger.error(
            f"Erreur récupération inscriptions utilisateur {user.id}: {e}"
        )
        logger.error(traceback.format_exc())

        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================
# Récupérer billet
# =============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mon_billet(request, inscription_id):
    try:

        billet = get_object_or_404(
            Billet.objects.select_related(
                "inscription",
                "inscription__evenement",
                "inscription__participant"
            ),
            inscription_id=inscription_id
        )

        serializer = BilletSerializer(billet)

        return Response(serializer.data)

    except Exception as e:

        logger.error(
            f"Erreur récupération billet {inscription_id} pour utilisateur {request.user.id}: {e}"
        )
        logger.error(traceback.format_exc())

        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================
# Télécharger PDF du billet
# =============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def telecharger_billet_pdf(request, inscription_id):

    try:

        billet = get_object_or_404(
            Billet.objects.select_related(
                "inscription",
                "inscription__evenement",
                "inscription__participant"
            ),
            inscription_id=inscription_id
        )

        buffer = BytesIO()
        p = canvas.Canvas(buffer)

        p.setFont("Helvetica-Bold", 16)
        p.drawString(
            100,
            750,
            f"Billet pour l'événement : {billet.inscription.evenement.titre}"
        )

        p.setFont("Helvetica", 12)

        p.drawString(
            100,
            720,
            f"Participant : {billet.inscription.participant.nom} {billet.inscription.participant.prenom}"
        )

        p.drawString(
            100,
            700,
            f"Date : {billet.inscription.evenement.date_debut}"
        )

        p.drawString(
            100,
            680,
            f"Lieu : {billet.inscription.evenement.lieu}"
        )

        # Ajouter QR code dans le PDF
        if billet.qr_code:
            p.drawImage(
                billet.qr_code.path,
                100,
                500,
                width=150,
                height=150
            )

        p.showPage()
        p.save()

        buffer.seek(0)

        response = HttpResponse(
            buffer,
            content_type="application/pdf"
        )

        response["Content-Disposition"] = (
            f'attachment; filename="billet_{billet.id}.pdf"'
        )

        return response

    except Exception as e:

        logger.error(f"Erreur téléchargement PDF billet {inscription_id}: {e}")
        logger.error(traceback.format_exc())

        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )