# apps/inscriptions/serializers.py

from rest_framework import serializers
from django.db import transaction

from .models import Inscription, Billet
from apps.payments.models import Paiement



# =====================================================
# SERIALIZER : BILLET
# =====================================================
# Permet de retourner les informations d'un billet :
# - QR Code
# - événement associé
# - informations de check-in
# =====================================================

class BilletSerializer(serializers.ModelSerializer):

    # Informations de l'événement liées au billet
    evenement_titre = serializers.CharField(
        source="inscription.evenement.titre",
        read_only=True
    )

    date_evenement = serializers.DateTimeField(
        source="inscription.evenement.date_debut",
        read_only=True
    )

    lieu = serializers.CharField(
        source="inscription.evenement.lieu",
        read_only=True
    )


    # Retourne l'URL complète du QR Code
    qr_code_url = serializers.SerializerMethodField()


    # Utilisateur du staff qui a effectué le scan
    scanne_par_nom = serializers.CharField(
        source="scanne_par.email",
        read_only=True
    )


    class Meta:
        model = Billet

        fields = [
            "id",
            "inscription",
            "qr_code_url",
            "date_emission",
            "utilise",
            "date_scan",
            "scanne_par",
            "scanne_par_nom",
            "evenement_titre",
            "date_evenement",
            "lieu"
        ]

        # Ces champs sont gérés automatiquement par le système
        read_only_fields = [
            "id",
            "date_emission",
            "date_scan",
            "scanne_par",
            "utilise"
        ]


    def get_qr_code_url(self, obj):
        """
        Génère l'URL publique du QR Code.
        """

        request = self.context.get('request')

        if obj.qr_code and request:
            return request.build_absolute_uri(obj.qr_code.url)

        return None






# =====================================================
# SERIALIZER : INSCRIPTION
# =====================================================
# Serializer utilisé pour afficher une inscription complète
# avec les informations du participant, événement et billet.
# =====================================================

class InscriptionSerializer(serializers.ModelSerializer):

    participant_nom = serializers.CharField(
        source="participant.nom",
        read_only=True
    )

    participant_prenom = serializers.CharField(
        source="participant.prenom",
        read_only=True
    )

    participant_email = serializers.EmailField(
        source="participant.email",
        read_only=True
    )


    # Informations événement
    evenement_titre = serializers.CharField(
        source="evenement.titre",
        read_only=True
    )

    evenement_prix = serializers.DecimalField(
        source="evenement.prix",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )


    # Libellé du statut
    # Exemple : paye -> Payé
    statut_label = serializers.CharField(
        source="get_statut_display",
        read_only=True
    )


    # Statut du paiement associé
    statut_paiement = serializers.CharField(
        source="paiement.statut",
        read_only=True
    )


    # Affiche le billet s'il existe
    billet = BilletSerializer(
        read_only=True
    )


    class Meta:

        model = Inscription

        fields = [
            "id",
            "participant",
            "participant_nom",
            "participant_prenom",
            "participant_email",
            "evenement",
            "evenement_titre",
            "evenement_prix",
            "date_inscription",
            "statut",
            "statut_label",
            "statut_paiement",
            "montant_paye",
            "reference_paiement",
            "paiement",
            "billet"
        ]


        # Champs contrôlés automatiquement
        read_only_fields = [
            "date_inscription",
            "reference_paiement",
            "montant_paye",
            "statut"
        ]







# =====================================================
# SERIALIZER : CREATION INSCRIPTION
# =====================================================
# Utilisé lorsqu'un participant s'inscrit.
#
# Etapes :
# 1- Vérification disponibilité événement
# 2- Création paiement en attente
# 3- Création inscription
# =====================================================

class InscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = Inscription

        fields = [
            "id",
            "evenement"
        ]

        read_only_fields = [
            "id"
        ]



    def validate(self, data):

        user = self.context["request"].user

        evenement = data["evenement"]



        # Vérifie si le participant possède déjà
        # une inscription active pour cet événement.
        if Inscription.objects.filter(
            participant=user,
            evenement=evenement
        ).exclude(statut='annule').exists():

            raise serializers.ValidationError(
                "Vous avez déjà une inscription en cours ou validée pour cet événement."
            )



        # Vérifie la capacité maximale
        if evenement.est_complet():

            raise serializers.ValidationError(
                "Désolé, cet événement est déjà complet."
            )



        # Vérifie que l'événement est publié
        if evenement.statut != 'publie':

            raise serializers.ValidationError(
                "Cet événement n'est pas ouvert aux inscriptions."
            )


        return data




    def create(self, validated_data):

        user = self.context["request"].user

        evenement = validated_data["evenement"]



        # Transaction atomique :
        # soit paiement + inscription sont créés,
        # soit aucune modification n'est enregistrée.
        with transaction.atomic():


            # Création du paiement en attente
            paiement = Paiement.objects.create(

                montant=evenement.prix,

                statut='en_attente',

                mode='stripe',

                description=(
                    f"Inscription : {evenement.titre} "
                    f"- {user.email}"
                )
            )



            # Création de l'inscription associée
            inscription = Inscription.objects.create(

                participant=user,

                evenement=evenement,

                montant_paye=0,

                paiement=paiement,

                statut='en_attente'
            )


        return inscription








# =====================================================
# SERIALIZER : CHECK-IN
# =====================================================
# Reçoit l'identifiant du billet scanné par le staff.
# =====================================================

class CheckInSerializer(serializers.Serializer):

    billet_id = serializers.UUIDField(
        help_text="L'ID unique du billet (UUID)"
    )







# =====================================================
# SERIALIZER : DASHBOARD PARTICIPANT
# =====================================================
# Retourne les informations affichées dans
# l'espace participant :
#
# - identité
# - événement
# - heure du check-in
# =====================================================

class ParticipantDashboardSerializer(serializers.ModelSerializer):


    prenom = serializers.CharField(
        source='participant.prenom',
        read_only=True
    )


    nom = serializers.CharField(
        source='participant.nom',
        read_only=True
    )


    email = serializers.CharField(
        source='participant.email',
        read_only=True
    )



    # Informations événement
    evenement = serializers.PrimaryKeyRelatedField(
        read_only=True
    )


    evenement_nom = serializers.CharField(
        source='evenement.titre',
        read_only=True
    )



    # Heure du scan du billet
    checkin_time = serializers.SerializerMethodField()



    class Meta:

        model = Inscription


        fields = [
            'id',
            'prenom',
            'nom',
            'email',
            'checkin_time',
            'evenement',
            'evenement_nom'
        ]



    def get_checkin_time(self, obj):

        # Vérifie si un billet existe
        if hasattr(obj, 'billet') and obj.billet:


            # Retourne la date du scan
            # uniquement si le billet a été utilisé.
            if obj.billet.utilise:

                return obj.billet.date_scan


        return None