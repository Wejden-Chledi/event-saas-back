# apps/feedback/services.py

from .models import Feedback, RapportIAEvenement, RapportGlobalOrganisation
from django.db.models import Avg
from apps.events.ai_service import get_openai_client
import os

def analyser_sentiment_avis(commentaire):
    """Analyse le sentiment d'un commentaire unique."""
    if not commentaire: return "Neutre"
    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "Tu es un analyseur de sentiments. Réponds uniquement par : Positif, Neutre ou Négatif."},
                {"role": "user", "content": commentaire}
            ],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except:
        return "Inconnu"

def generer_rapport_ia_evenement(evenement):
    """Analyse intelligente et aide à la décision pour UN événement."""
    feedbacks = Feedback.objects.filter(evenement=evenement)
    if not feedbacks.exists(): return "Pas de données."

    stats = feedbacks.aggregate(avg=Avg('note_globale'), org=Avg('organisation'), cont=Avg('contenu'))
    commentaires = "\n".join([f"- {f.sentiment_ia}: {f.commentaire}" for f in feedbacks if f.commentaire])

    prompt = f"""
    Analyse les feedbacks pour l'événement '{evenement.titre}'.
    Stats: Note moyenne {stats['avg']}/5.
    Commentaires: {commentaires}
    
    Format de réponse JSON:
    {{
      "analyse": "résumé intelligent des retours",
      "decision": "3 conseils concrets pour le prochain événement"
    }}
    """

    client = get_openai_client()
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "system", "content": "Tu es un expert en stratégie événementielle. Réponds en JSON."},
                  {"role": "user", "content": prompt}]
    )
    
    import json
    data = json.loads(response.choices[0].message.content)

    rapport, _ = RapportIAEvenement.objects.update_or_create(
        evenement=evenement,
        defaults={'resume_ia': data['analyse'], 'aide_decision': data['decision']}
    )
    return rapport

def generer_analyse_globale_organisation(organisation):
    """Analyse transversale de tous les événements pour le propriétaire."""
    evenements = organisation.evenement_set.all()
    synthese = ""
    for e in evenements:
        avg = Feedback.objects.filter(evenement=e).aggregate(Avg('note_globale'))['note_globale__avg']
        synthese += f"- {e.titre}: {avg if avg else 'N/A'}/5\n"

    prompt = f"Analyse la performance globale de l'organisation {organisation.nom} basée sur ces résultats :\n{synthese}\nDonne une analyse stratégique pour l'avenir."

    client = get_openai_client()
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "user", "content": prompt}]
    )
    
    analyse = response.choices[0].message.content
    rapport, _ = RapportGlobalOrganisation.objects.update_or_create(
        organisation=organisation,
        defaults={'analyse_strategique': analyse}
    )
    return analyse