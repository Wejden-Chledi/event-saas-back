# ============================================================================
# Fichier : apps/feedback/services.py
#
# Ce fichier contient les services métier liés au module Feedback.
#
# Il assure :
#
#   - L'analyse automatique des sentiments des commentaires participants
#     grâce à Azure OpenAI.
#
#   - La génération de rapports IA détaillés pour un événement :
#       * Analyse des notes moyennes.
#       * Synthèse des commentaires.
#       * Recommandations stratégiques.
#
#   - La génération d'une analyse globale pour une organisation :
#       * Agrégation des résultats de plusieurs événements.
#       * Production d'une synthèse stratégique avec l'IA.
#
# Ces services permettent d'ajouter une couche d'intelligence artificielle
# afin d'aider les gestionnaires à améliorer la qualité des événements.
# ============================================================================
# ============================================================================
# Fichier : apps/feedback/services.py
# ============================================================================

import json
import logging
import os

from django.db.models import Avg

from .models import (
    Feedback,
    RapportIAEvenement,
    RapportGlobalOrganisation
)

from apps.events.models import Evenement
from apps.events.ai_service import get_openai_client

logger = logging.getLogger(__name__)

def analyser_sentiment_avis(commentaire):
    """Analyse le sentiment d'un commentaire participant."""
    if not commentaire:
        return "Neutre"

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un analyseur de sentiments. Réponds uniquement par un seul mot : Positif, Neutre ou Négatif."
                },
                {
                    "role": "user",
                    "content": commentaire
                }
            ],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Neutre"

def generer_rapport_ia_evenement(evenement_id):
    """Génère un rapport intelligent pour un événement spécifique."""
    if isinstance(evenement_id, int):
        try:
            evenement = Evenement.objects.get(id=evenement_id)
        except Evenement.DoesNotExist:
            return "Événement introuvable."
    else:
        evenement = evenement_id

    feedbacks = Feedback.objects.filter(evenement=evenement)
    if not feedbacks.exists():
        return "Pas assez de feedbacks pour générer un rapport."
    stats = feedbacks.aggregate( avg=Avg('note_globale'),org=Avg('organisation'),cont=Avg('contenu'))
    commentaires = "\n".join([ f"- {getattr(f, 'sentiment_ia', 'Neutre')}: {f.commentaire}"
            for f in feedbacks.exclude(commentaire="")[:15]])
    prompt = f"""
    Analyse les feedbacks pour l'événement '{evenement.titre}'.
    Statistiques moyennes : Note {stats['avg']}/5, Organisation {stats['org']}/5, Contenu {stats['cont']}/5.
    Commentaires participants :
    {commentaires}
    Réponds EXCLUSIVEMENT au format JSON :
    {{"analyse": "résumé",
      "decision": "conseils" }}
    """
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system","content": "Tu es un expert en stratégie événementielle. Tu ne parles qu'en JSON."},
                {"role": "user","content": prompt}])

        content = response.choices[0].message.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        data = json.loads(content)

        rapport_obj, _ = RapportIAEvenement.objects.update_or_create(
            evenement=evenement,
            defaults={
                'resume_ia': data.get('analyse', "Analyse indisponible"),
                'aide_decision': data.get('decision', "Conseils indisponibles")
            }
        )

        return rapport_obj.resume_ia

    except Exception as e:
        logger.error(f"Erreur IA Event: {e}")
        return f"Erreur lors de la génération : {str(e)}"

def generer_analyse_globale_organisation(organisation):
    """Génère une analyse stratégique globale d'une organisation."""
    evenements = Evenement.objects.filter(organisation=organisation)
    if not evenements.exists():
        return "Aucune donnée disponible pour l'organisation."
    synthese = ""
    for e in evenements:
        stats = Feedback.objects.filter(evenement=e).aggregate(avg=Avg('note_globale'))
        avg = stats['avg']
        synthese += f"- {e.titre}: {round(avg, 1) if avg else 'Pas d avis'}/5\n"
    prompt = f"Analyse stratégique pour '{organisation.nom}':\n{synthese}"
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "user","content": prompt}])
        analyse = response.choices[0].message.content

        RapportGlobalOrganisation.objects.update_or_create(
            organisation=organisation,
            defaults={
                'analyse_strategique': analyse
            }
        )

        return analyse

    except Exception as e:
        return f"Erreur : {str(e)}"