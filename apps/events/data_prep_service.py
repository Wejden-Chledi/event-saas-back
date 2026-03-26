# apps/events/data_prep_service.py
import re
from typing import Dict, List, Optional, Any
from .models import Evenement
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  

class EventDataPreparer:
    """Prépare et nettoie les données événements pour l'IA."""

    def __init__(self):
        self.stop_words = set([
            'le', 'la', 'les', 'de', 'des', 'du', 'au', 'aux', 'et', 'ou', 'mais', 
            'donc', 'or', 'ni', 'car', 'un', 'une', 'dans', 'sur', 'sous', 'avec', 
            'pour', 'par', 'vers', 'entre', 'chez', 'pendant'
        ])

    # Nettoyage
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\sàáâäãåçèéêëìíîïñòóôöõùúûüýÿ]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return ' '.join([w for w in text.split() if w not in self.stop_words])

    # Catégorisation
    def categorize_event(self, event_data: Dict[str, Any]) -> str:
        text = f"{event_data.get('titre', '')} {event_data.get('description', '')}"
        text = self.clean_text(text)
        keywords = [w for w in text.split() if len(w) > 3]

        categories = {
            'technologie': ['tech', 'numérique', 'digital', 'ia', 'artificielle', 'logiciel', 'web', 'code', 'programmation'],
            'business': ['business', 'entreprise', 'startup', 'finance', 'marketing', 'vente', 'stratégie', 'management'],
            'formation': ['formation', 'cours', 'atelier', 'workshop', 'éducation'],
            'social': ['réseau', 'rencontre', 'social', 'communauté', 'partage'],
            'culture': ['culture', 'art', 'musique', 'cinéma', 'théâtre', 'exposition', 'festival'],
            'sport': ['sport', 'compétition', 'course', 'match', 'tournoi', 'athlète'],
            'santé': ['santé', 'bien-être', 'médical', 'soin', 'thérapie', 'fitness']
        }

        for cat, kw_list in categories.items():
            if any(k in keywords for k in kw_list):
                return cat
        return 'divers'

    # -----------------------------
    # Détection de la langue
    # -----------------------------
    def detect_language(self, text: str) -> str:
        """
        Détecte la langue d'un texte.
        Retourne 'fr' pour français, 'en' pour anglais, ou 'other' sinon.
        """
        try:
            lang = detect(text)
            if lang.startswith('fr'):
                return 'fr'
            elif lang.startswith('en'):
                return 'en'
            return 'other'
        except:
            return 'other'

    # -----------------------------
    # Prompt structuré amélioré
    # -----------------------------
    def build_structured_prompt(self, event_data: Dict[str, Any]) -> str:
        category = self.categorize_event(event_data)
        titre = event_data.get('titre', '')
        description = event_data.get('description', '')
        lieu = event_data.get('lieu', '')
        prix = event_data.get('prix', 0)
        capacite = event_data.get('capacite_max', 0)
        date_debut = event_data.get('date_debut', 'à définir')
        date_fin = event_data.get('date_fin', 'à définir')

        # Détection de langue
        langue = self.detect_language(titre)
        if langue == 'en':
            prompt = f"""
Title: {titre}
Description: {description}
Location: {lieu}
Price: {prix}€
Capacity: {capacite} participants
Category: {category}
Dates: {date_debut} - {date_fin}

Generate a professional and engaging event description in English.
"""
        else:
            prompt = f"""
Titre: {titre}
Description: {description}
Lieu: {lieu}
Prix: {prix}€
Capacité: {capacite} participants
Catégorie: {category}
Dates: {date_debut} - {date_fin}

Génère une description professionnelle et engageante en français.
"""
        return prompt