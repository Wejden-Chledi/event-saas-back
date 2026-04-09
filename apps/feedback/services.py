# apps/feedback/services.py

from .models import Feedback, RapportIAEvenement
from django.db.models import Avg
from apps.events.ai_service import get_openai_client
import os

def generer_rapport_ia_evenement(evenement):

    feedbacks = Feedback.objects.filter(evenement=evenement)

    if not feedbacks.exists():
        return "Pas assez de données."

    stats = feedbacks.aggregate(
        avg_globale=Avg('note_globale'),
        avg_org=Avg('organisation'),
        avg_contenu=Avg('contenu'),
        avg_speakers=Avg('intervenants'),
        avg_lieu=Avg('lieu'),
        avg_ambiance=Avg('ambiance'),
        avg_prix=Avg('rapport_qualite_prix')
    )

    recommande_count = feedbacks.filter(recommande=True).count()
    total = feedbacks.count()
    taux_recommandation = (recommande_count / total) * 100

    commentaires = "\n".join([
        f"- {f.commentaire}" for f in feedbacks if f.commentaire
    ])

    prompt = f"""
    Tu es un expert en analyse d'événements.

    Objectif :
    Fournir un rapport clair et actionnable.

    Analyse :
    - Points forts (notes >= 4)
    - Points faibles (notes <= 3)
    - Suggestions concrètes
    - Résumé des commentaires

    Données :
    Score global: {stats['avg_globale']}
    Organisation: {stats['avg_org']}
    Contenu: {stats['avg_contenu']}
    Intervenants: {stats['avg_speakers']}
    Lieu: {stats['avg_lieu']}
    Ambiance: {stats['avg_ambiance']}
    Prix: {stats['avg_prix']}
    Taux recommandation: {taux_recommandation}%

    Commentaires:
    {commentaires}
    """

    client = get_openai_client()

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "Expert analyse événementielle"},
            {"role": "user", "content": prompt}
        ]
    )

    analyse = response.choices[0].message.content

    rapport, _ = RapportIAEvenement.objects.update_or_create(
        evenement=evenement,
        defaults={
            'resume_ia': analyse,
            'statut': 'done'
        }
    )

    return analyse