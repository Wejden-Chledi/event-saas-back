# ============================================================================
# Fichier : apps/organisations/views/abonnement_views.py
#
# Ce fichier contient les vues permettant de gérer les abonnements
# associés aux organisations.
#
# Fonctionnalités :
#
#   - Modifier l'abonnement d'une organisation
#   - Consulter les informations de l'abonnement actuel
#
# Les opérations sensibles (modification) sont réservées
# au propriétaire de l'organisation.
# ============================================================================



# ==============================
# IMPORTATION DES LIBRAIRIES DRF
# ==============================

# Décorateurs permettant de créer des vues basées sur des fonctions
# et d'appliquer des permissions.
from rest_framework.decorators import api_view, permission_classes


# Permet de retourner des réponses HTTP au format JSON.
from rest_framework.response import Response



# ==============================
# IMPORTATION DES MODELES
# ==============================

# Modèle représentant une organisation cliente.
from apps.organisations.models import Organisation



# ==============================
# IMPORTATION DES SERIALIZERS
# ==============================

# Serializer utilisé pour transformer un abonnement
# en données JSON.
from apps.organisations.serializers import AbonnementSerializer



# ==============================
# IMPORTATION DES PERMISSIONS
# ==============================

# Permission personnalisée permettant de vérifier
# que l'utilisateur connecté est propriétaire.
from apps.users.permissions import IsProprietaire


# Permission nécessitant une authentification.
from rest_framework.permissions import IsAuthenticated



# ==============================
# IMPORTATION DES OUTILS DATE
# ==============================

# Permet de manipuler les dates et calculer
# les durées des abonnements.
from datetime import datetime, timedelta




# ============================================================================
# CONFIGURATION DES PLANS D'ABONNEMENT
# ============================================================================


# Association entre chaque plan et sa durée en jours.
#
# Exemple :
#   - abonnement gratuit : 30 jours
#   - abonnement pro : 90 jours
duree_map = {

    "gratuit": 30,

    "basique": 30,

    "pro": 90,

    "premium": 365

}



# Prix associés aux différents plans.
PLAN_PRICES = {

    "gratuit": 0,

    "basique": 50,

    "pro": 140,

    "premium": 500

}





# ============================================================================
# UPDATE ABONNEMENT
# ============================================================================
#
# Permet au propriétaire d'une organisation
# de modifier son abonnement.
#
# Méthode HTTP :
#       PUT
#
# Accès :
#       Utilisateur authentifié + Propriétaire
#
# ============================================================================


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsProprietaire])
def update_abonnement_view(request):


    # Récupération de l'utilisateur connecté.
    user = request.user



    # Recherche de l'organisation appartenant
    # au propriétaire connecté.
    try:

        organisation = Organisation.objects.get(
            proprietaire=user
        )


    # Si aucune organisation n'est trouvée.
    except Organisation.DoesNotExist:

        return Response(
            {
                "error": "Organisation non trouvée"
            },
            status=404
        )



    # Récupération de l'abonnement associé.
    abonnement = organisation.abonnement



    # Vérification de l'existence d'un abonnement.
    if not abonnement:

        return Response(
            {
                "error": "Aucun abonnement"
            },
            status=400
        )



    # Récupération des données envoyées
    # dans la requête HTTP.
    data = request.data




    # ------------------------------------------------------------------------
    # Modification du plan d'abonnement
    # ------------------------------------------------------------------------

    if "plan" in data:


        # Récupération du nouveau plan.
        plan = data["plan"]


        # Mise à jour du plan.
        abonnement.plan = plan



        # Mise à jour automatique du montant
        # selon le plan choisi.
        abonnement.montant = PLAN_PRICES.get(
            plan,
            0
        )



        # Si la date de début n'existe pas,
        # elle est initialisée avec la date actuelle.
        #
        # Ensuite, la date de fin est calculée
        # selon la durée du nouveau plan.
        if not abonnement.date_debut:

            abonnement.date_debut = datetime.now().date()


        abonnement.date_fin = (
            abonnement.date_debut
            +
            timedelta(
                days=duree_map.get(plan, 30)
            )
        )



    # ------------------------------------------------------------------------
    # Modification du statut
    # ------------------------------------------------------------------------

    if "statut" in data:

        # Mise à jour du statut :
        # actif, suspendu ou expire.
        abonnement.statut = data["statut"]





    # ------------------------------------------------------------------------
    # Modification manuelle de la date de fin
    # ------------------------------------------------------------------------

    if "date_fin" in data:

        try:

            # Conversion de la date reçue au format :
            # YYYY-MM-DD
            abonnement.date_fin = (
                datetime.fromisoformat(
                    data["date_fin"]
                ).date()
            )


        # Si le format est incorrect,
        # aucune modification n'est appliquée.
        except ValueError:

            pass




    # Enregistrement des modifications
    # dans la base de données.
    abonnement.save()



    # Retourne un message de confirmation
    # avec les nouvelles informations.
    return Response(
        {
            "message": "Abonnement mis à jour",

            "abonnement":
                AbonnementSerializer(abonnement).data
        }
    )






# ============================================================================
# GET ABONNEMENT
# ============================================================================
#
# Permet à un utilisateur authentifié
# de consulter l'abonnement de son organisation.
#
# Méthode HTTP :
#       GET
#
# ============================================================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_abonnement_view(request):


    # Utilisateur connecté.
    user = request.user



    # Recherche de l'organisation associée.
    #
    # Cas 1 :
    # L'utilisateur n'est pas propriétaire :
    #     on récupère directement son organisation.
    #
    # Cas 2 :
    # L'utilisateur est propriétaire :
    #     on recherche l'organisation qu'il possède.
    organisation = (
        user.organisation
        if user.role != "proprietaire"
        else
        Organisation.objects.filter(
            proprietaire=user
        ).first()
    )



    # Vérification de l'existence de l'organisation
    # et de son abonnement.
    if not organisation or not organisation.abonnement:

        return Response(
            {
                "error": "Aucun abonnement"
            },
            status=404
        )



    # Retourne les informations de l'abonnement
    # sous forme JSON.
    return Response(
        AbonnementSerializer(
            organisation.abonnement
        ).data
    )