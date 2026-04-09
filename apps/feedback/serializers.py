# apps/feedback/serializers.py
from rest_framework import serializers
from .models import Feedback, RapportIAEvenement
from apps.inscriptions.models import Inscription

class FeedbackSerializer(serializers.ModelSerializer):
    # Récupération précise selon ton modèle Utilisateur
    participant_nom = serializers.SerializerMethodField()
    participant_email = serializers.ReadOnlyField(source='participant.email')
    participant = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Feedback
        fields = [
            'id', 'evenement', 'participant', 'participant_nom', 'participant_email',
            'organisation', 'contenu', 'intervenants', 'note_globale',
            'lieu', 'ambiance', 'rapport_qualite_prix',
            'commentaire', 'recommande', 'date_creation'
        ]
        read_only_fields = ['id', 'note_globale', 'sentiment_ia', 'date_creation']

    def get_participant_nom(self, obj):
        """Utilise les champs nom et prenom de ton modèle Utilisateur"""
        user = obj.participant
        nom = getattr(user, 'nom', '').strip()
        prenom = getattr(user, 'prenom', '').strip()
        
        if nom or prenom:
            return f"{prenom} {nom}".strip()
        
        # Fallback sur l'email si nom/prenom sont vides
        return user.email.split('@')[0]

    def validate(self, data):
        user = self.context['request'].user
        evenement = data['evenement']

        # Vérification basée sur ton modèle Inscription (statut='utilise')
        try:
            Inscription.objects.get(
                participant=user,
                evenement=evenement,
                statut='utilise'
            )
        except Inscription.DoesNotExist:
            raise serializers.ValidationError(
                "Accès refusé : Seuls les participants ayant scanné leur billet peuvent laisser un avis."
            )

        if Feedback.objects.filter(participant=user, evenement=evenement).exists():
            raise serializers.ValidationError("Vous avez déjà soumis un avis pour cet événement.")

        return data

    def create(self, validated_data):
        notes = [
            validated_data['organisation'], validated_data['contenu'],
            validated_data['intervenants'], validated_data['lieu'],
            validated_data['ambiance'], validated_data['rapport_qualite_prix']
        ]
        # Calcul de la moyenne entière
        validated_data['note_globale'] = sum(notes) // len(notes)
        return super().create(validated_data)

class RapportIASerializer(serializers.ModelSerializer):
    evenement_titre = serializers.ReadOnlyField(source='evenement.titre')
    
    class Meta:
        model = RapportIAEvenement
        fields = ['id', 'evenement', 'evenement_titre', 'resume_ia', 'points_amelioration', 'date_generation']