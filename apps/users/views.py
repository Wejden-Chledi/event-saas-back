# apps/users/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import ProprietaireRegisterSerializer, ParticipantRegisterSerializer
from django.utils import timezone
from datetime import timedelta
from apps.organisations.models import Abonnement
from apps.organisations.models import Organisation
Utilisateur = get_user_model()


# -----------------------------
# LOGIN avec JWT
# -----------------------------
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user

            # Générer les tokens
            refresh = RefreshToken.for_user(user)

            # Construire la réponse
            user_data = {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role,
                "telephone": getattr(user, "telephone", ""),
            }

            response_data = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_data,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# LOGOUT JWT
# -----------------------------
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token requis"}, status=400)
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Déconnecté avec succès"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)


# -----------------------------
# PROFIL utilisateur
# -----------------------------
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    user = request.user
    data = {
        "id": user.id,
        "email": user.email,
        "nom": user.nom,
        "prenom": user.prenom,
        "role": user.role,
        "telephone": getattr(user, "telephone", ""),
        "statut": user.statut,
    }

    # Organisation si propriétaire
    if hasattr(user, "organisation_proprietaire"):
        org = user.organisation_proprietaire
        data["organisation"] = {
            "id": org.id,
            "nom": org.nom,
            "secteur": org.secteur,
            "email_contact": org.emailContact,
            "telephone_organisation": org.telephone,
            "adresse": org.adresse,
            "ville": org.ville,
            "pays": org.pays,
            "site_web": org.siteWeb,
            "statutAbonnement": org.statutAbonnement,
            "abonnement": {
                "type": org.abonnement.type,
                "dateDebut": org.abonnement.dateDebut,
                "dateFin": org.abonnement.dateFin,
                "montant": org.abonnement.montant,
            },
        }

    return Response(data)

# -----------------------------
# INSCRIPTION propriétaire
# -----------------------------
@api_view(["POST"])
def register_proprietaire_view(request):
    serializer = ProprietaireRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "Compte propriétaire créé avec succès",
            "user": {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role,
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# INSCRIPTION participant
# -----------------------------
@api_view(["POST"])
def register_participant_view(request):
    serializer = ParticipantRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "Compte participant créé avec succès",
            "user": {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role,
                "telephone": getattr(user, "telephone", ""),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# INSCRIPTION générique
# -----------------------------
@api_view(["POST"])
def register_view(request):
    data = request.data

    if "nom_organisation" in data and "secteur" in data:
        serializer = ProprietaireRegisterSerializer(data=data)
        message = "Compte propriétaire créé avec succès"
    else:
        serializer = ParticipantRegisterSerializer(data=data)
        message = "Compte participant créé avec succès"

    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": message,
            "user": {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role,
            }
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["PUT"])
@permission_classes([permissions.IsAuthenticated])
def update_proprietaire_view(request):
    user = request.user
    data = request.data

    # --- mise à jour des infos personnelles ---
    user.nom = data.get("nom", user.nom)
    user.prenom = data.get("prenom", user.prenom)
    user.email = data.get("email", user.email)
    user.telephone = data.get("telephone", user.telephone)

    password = data.get("password")
    if password:
        user.set_password(password) 

    user.save()

    return Response({
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "telephone": user.telephone
    })


@api_view(["PUT"])
@permission_classes([permissions.IsAuthenticated])
def update_abonnement_view(request):
    user = request.user

    # Récupérer la première organisation du propriétaire
    org = user.organisations.first()
    if not org:
        return Response({"error": "Utilisateur n'a pas d'organisation"}, status=400)

    type_abonnement = request.data.get("type_abonnement")
    if not type_abonnement:
        return Response({"error": "type_abonnement requis"}, status=400)

    # Mapper la durée et le montant selon le type
    duree_mois_map = {"gratuit": 1, "basique": 1, "pro": 3, "premium": 12}
    montant_map = {"gratuit": 0, "basique": 50.0, "pro": 140.0, "premium": 500.0}

    if type_abonnement not in duree_mois_map:
        return Response({"error": "Type d'abonnement invalide"}, status=400)

    duree_mois = duree_mois_map[type_abonnement]
    montant = montant_map[type_abonnement]

    date_debut = timezone.now().date()
    date_fin = date_debut + timedelta(days=30 * duree_mois)

    # Créer ou mettre à jour l'abonnement
    if org.abonnement:
        abonnement = org.abonnement
        abonnement.type = type_abonnement
        abonnement.dateDebut = date_debut
        abonnement.dateFin = date_fin
        abonnement.montant = montant
        abonnement.statut = 'actif'
        abonnement.save()
    else:
        abonnement = Abonnement.objects.create(
            type=type_abonnement,
            dateDebut=date_debut,
            dateFin=date_fin,
            montant=montant,
            statut='actif'
        )
        org.abonnement = abonnement

    org.statutAbonnement = 'actif'
    org.save()

    return Response({
        "message": "Abonnement mis à jour avec succès",
        "abonnement": {
            "type": abonnement.type,
            "dateDebut": abonnement.dateDebut,
            "dateFin": abonnement.dateFin,
            "montant": abonnement.montant,
        }
    })