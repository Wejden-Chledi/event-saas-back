# ============================================================================
# Fichier : apps/feedback/serializers.py
#
# Ce fichier contient les serializers liés au module Feedback.
#
# Il définit :
#
#   - FeedbackSerializer :
#       Sérialisation et validation des avis déposés par les participants.
#       Il calcule automatiquement la note globale et intègre l'analyse
#       de sentiment réalisée par l'intelligence artificielle.
#
#   - RapportIASerializer :
#       Sérialisation des rapports d'analyse IA générés pour les événements.
#
# Ce module assure :
#   - La validation des conditions de dépôt d'un feedback.
#   - La vérification qu'un participant a bien assisté à l'événement.
#   - La prévention des avis multiples pour un même événement.
#   - L'intégration des résultats d'analyse IA.
# ============================================================================


from rest_framework import serializers
from .models import Feedback, RapportIAEvenement
from apps.inscriptions.models import Inscription
from .services import analyser_sentiment_avis


class FeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer permettant de gérer les avis des participants.

    Il ajoute des informations supplémentaires sur le participant
    et applique des règles métier avant l'enregistrement.
    """

    # Informations affichées concernant le participant
    participant_nom = serializers.SerializerMethodField()
    participant_email = serializers.ReadOnlyField(source='participant.email')

    # Le participant est récupéré automatiquement depuis l'utilisateur connecté
    participant = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Feedback

        fields = [
            'id', 'evenement', 'participant', 'participant_nom',
            'participant_email',
            'organisation', 'contenu', 'intervenants',
            'note_globale', 'lieu', 'ambiance',
            'rapport_qualite_prix',
            'commentaire', 'recommande',
            'sentiment_ia', 'date_creation'
        ]

        # Ces champs sont calculés automatiquement
        read_only_fields = [
            'id',
            'note_globale',
            'sentiment_ia',
            'date_creation'
        ]


    def get_participant_nom(self, obj):
        """
        Retourne le nom complet du participant.
        Si le nom n'est pas disponible, utilise la partie avant l'email.
        """

        user = obj.participant

        nom = getattr(user, 'nom', '').strip()
        prenom = getattr(user, 'prenom', '').strip()

        if nom or prenom:
            return f"{prenom} {nom}".strip()

        return user.email.split('@')[0]


    def validate(self, data):
        """
        Validation métier avant création du feedback.

        Vérifie :
        - Que le participant a réellement assisté à l'événement.
        - Qu'il n'a pas déjà envoyé un avis.
        """

        user = self.context['request'].user
        evenement = data['evenement']


        # Vérifie que le billet du participant a été utilisé (check-in effectué)
        try:
            Inscription.objects.get(
                participant=user,
                evenement=evenement,
                statut='utilise'
            )

        except Inscription.DoesNotExist:
            raise serializers.ValidationError(
                "Seuls les participants ayant scanné leur billet peuvent laisser un avis."
            )


        # Empêche un participant de donner plusieurs avis pour un même événement
        if Feedback.objects.filter(
            participant=user,
            evenement=evenement
        ).exists():

            raise serializers.ValidationError(
                "Vous avez déjà soumis un avis pour cet événement."
            )


        return data


    def create(self, validated_data):
        """
        Création du feedback avec traitements automatiques :

        - Calcul de la note moyenne globale.
        - Analyse du sentiment du commentaire par IA.
        """

        # Calcul automatique de la note globale à partir des critères
        notes = [
            validated_data['organisation'],
            validated_data['contenu'],
            validated_data['intervenants'],
            validated_data['lieu'],
            validated_data['ambiance'],
            validated_data['rapport_qualite_prix']
        ]

        validated_data['note_globale'] = sum(notes) // len(notes)


        # Analyse automatique du commentaire avec le service IA
        commentaire = validated_data.get('commentaire', '')

        validated_data['sentiment_ia'] = analyser_sentiment_avis(
            commentaire
        )


        return super().create(validated_data)



class RapportIASerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher les rapports d'analyse IA des événements.
    """

    # Affichage du titre de l'événement associé
    evenement_titre = serializers.ReadOnlyField(
        source='evenement.titre'
    )


    class Meta:
        model = RapportIAEvenement

        fields = [
            'id',
            'evenement',
            'evenement_titre',
            'resume_ia',
            'aide_decision',
            'date_generation'
        ]