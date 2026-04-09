# apps/feedback/serializers.py
from rest_framework import serializers
from .models import Feedback, RapportIAEvenement
from apps.inscriptions.models import Inscription
from .services import analyser_sentiment_avis

class FeedbackSerializer(serializers.ModelSerializer):
    participant_nom = serializers.SerializerMethodField()
    participant_email = serializers.ReadOnlyField(source='participant.email')
    participant = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Feedback
        fields = [
            'id', 'evenement', 'participant', 'participant_nom', 'participant_email',
            'organisation', 'contenu', 'intervenants', 'note_globale',
            'lieu', 'ambiance', 'rapport_qualite_prix',
            'commentaire', 'recommande', 'sentiment_ia', 'date_creation'
        ]
        read_only_fields = ['id', 'note_globale', 'sentiment_ia', 'date_creation']

    def get_participant_nom(self, obj):
        user = obj.participant
        nom = getattr(user, 'nom', '').strip()
        prenom = getattr(user, 'prenom', '').strip()
        if nom or prenom:
            return f"{prenom} {nom}".strip()
        return user.email.split('@')[0]

    def validate(self, data):
        user = self.context['request'].user
        evenement = data['evenement']

        # Vérifier que le participant a bien été scanné
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

        # Empêcher les doublons
        if Feedback.objects.filter(participant=user, evenement=evenement).exists():
            raise serializers.ValidationError("Vous avez déjà soumis un avis pour cet événement.")

        return data

    def create(self, validated_data):
        # Calcul de la moyenne automatique
        notes = [
            validated_data['organisation'], validated_data['contenu'],
            validated_data['intervenants'], validated_data['lieu'],
            validated_data['ambiance'], validated_data['rapport_qualite_prix']
        ]
        validated_data['note_globale'] = sum(notes) // len(notes)
        
        # IA : Analyse automatique du sentiment du commentaire avant sauvegarde
        commentaire = validated_data.get('commentaire', '')
        validated_data['sentiment_ia'] = analyser_sentiment_avis(commentaire)
        
        return super().create(validated_data)

class RapportIASerializer(serializers.ModelSerializer):
    evenement_titre = serializers.ReadOnlyField(source='evenement.titre')
    
    class Meta:
        model = RapportIAEvenement
        fields = ['id', 'evenement', 'evenement_titre', 'resume_ia', 'aide_decision', 'date_generation']