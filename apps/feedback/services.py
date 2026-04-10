# apps/feedback/services.py
from .models import Feedback, RapportIAEvenement, RapportGlobalOrganisation
from django.db.models import Avg
from apps.events.ai_service import get_openai_client
import os
import json

def analyser_sentiment_avis(commentaire):
    """Analyse le sentiment d'un commentaire unique via Azure OpenAI."""
    if not commentaire: return "Neutre"
    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "Tu es un analyseur de sentiments. Réponds uniquement par un seul mot : Positif, Neutre ou Négatif."},
                {"role": "user", "content": commentaire}
            ],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Neutre"

def generer_rapport_ia_evenement(evenement):
    """Analyse intelligente et aide à la décision pour UN événement."""
    feedbacks = Feedback.objects.filter(evenement=evenement)
    if not feedbacks.exists():
        return None

    stats = feedbacks.aggregate(
        avg=Avg('note_globale'), 
        org=Avg('organisation'), 
        cont=Avg('contenu')
    )
    
    # On limite à 15 commentaires pour ne pas dépasser les tokens
    commentaires = "\n".join([f"- {f.sentiment_ia}: {f.commentaire}" for f in feedbacks.exclude(commentaire="")[:15]])

    prompt = f"""
    Analyse les feedbacks pour l'événement '{evenement.titre}'.
    Statistiques moyennes : Note {stats['avg']}/5, Organisation {stats['org']}/5, Contenu {stats['cont']}/5.
    Commentaires participants :
    {commentaires}
    
    Réponds EXCLUSIVEMENT au format JSON :
    {{
      "analyse": "un résumé de 3 phrases sur l'ambiance et la satisfaction",
      "decision": "3 conseils stratégiques numérotés pour s'améliorer"
    }}
    """

    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[{"role": "system", "content": "Tu es un expert en stratégie événementielle. Tu ne parles qu'en JSON."},
                      {"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content
        # Nettoyage si l'IA ajoute des balises ```json
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
            
        data = json.loads(content)

        rapport, _ = RapportIAEvenement.objects.update_or_create(
            evenement=evenement,
            defaults={
                'resume_ia': data.get('analyse', "Analyse indisponible"), 
                'aide_decision': data.get('decision', "Conseils indisponibles")
            }
        )
        return rapport
    except Exception as e:
        print(f"Erreur IA Event: {e}")
        return None

def generer_analyse_globale_organisation(organisation):
    """Analyse transversale corrigée (évite l'erreur AttributeError sur evenement_set)."""
    from apps.events.models import Evenement
    
    # Correction ici : Utilisation du filtre direct sur le modèle Evenement
    evenements = Evenement.objects.filter(organisation=organisation)
    
    if not evenements.exists():
        return "Aucune donnée disponible pour l'organisation."

    synthese = ""
    for e in evenements:
        stats = Feedback.objects.filter(evenement=e).aggregate(Avg('note_globale'))
        avg = stats['note_globale__avg']
        synthese += f"- {e.titre}: {round(avg, 1) if avg else 'Pas d avis'}/5\n"

    prompt = f"""
    En tant que consultant senior, analyse la performance globale de l'organisation '{organisation.nom}'.
    Voici les notes moyennes par événement :
    {synthese}
    
    Donne une analyse stratégique globale et des axes de développement pour l'année prochaine.
    """

    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[{"role": "user", "content": prompt}]
        )
        
        analyse = response.choices[0].message.content
        
        RapportGlobalOrganisation.objects.update_or_create(
            organisation=organisation,
            defaults={'analyse_strategique': analyse}
        )
        return analyse
    except Exception as e:
        return f"Erreur lors de l'analyse globale : {str(e)}"