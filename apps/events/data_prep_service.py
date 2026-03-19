import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from django.utils import timezone
from .models import Evenement

class EventDataPreparer:
    """Service avancé pour préparer et enrichir les données événements pour l'IA et l'affichage."""

    def __init__(self):
        self.stop_words = set([
            'le', 'la', 'les', 'de', 'des', 'du', 'au', 'aux', 'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car',
            'un', 'une', 'dans', 'sur', 'sous', 'avec', 'pour', 'par', 'vers', 'entre', 'chez', 'pendant'
        ])

    # -----------------------------
    # Extraction et nettoyage
    # -----------------------------
    def get_event_data(self, event_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupère les événements depuis la base et retourne une liste de dicts."""
        events = Evenement.objects.filter(id=event_id) if event_id else Evenement.objects.all()
        return [
            {
                'id': e.id,
                'titre': e.titre,
                'description': e.description,
                'lieu': e.lieu,
                'statut': e.statut,
                'date_debut': e.date_debut,
                'date_fin': e.date_fin,
                'capacite_max': e.capacite_max,
                'prix': float(e.prix),
                'organisation': e.organisation.nom if e.organisation else None,
                'createur': f"{e.createur.nom} {e.createur.prenom}" if e.createur else None
            }
            for e in events
        ]

    def clean_text(self, text: str) -> str:
        """Nettoie un texte: minuscules, suppression ponctuation et stop words."""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\sàáâäãåçèéêëìíîïñòóôöõùúûüýÿ]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        words = [w for w in text.split() if w not in self.stop_words]
        return ' '.join(words)

    # -----------------------------
    # Mots-clés et analyse
    # -----------------------------
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extrait les mots-clés les plus fréquents et pertinents d’un texte."""
        cleaned = self.clean_text(text)
        freq = {}
        for word in cleaned.split():
            if len(word) > 3:  # mots significatifs
                freq[word] = freq.get(word, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_keywords]]

    def categorize_event(self, event_data: Dict[str, Any]) -> str:
        """Catégorise un événement selon ses mots-clés."""
        keywords = self.extract_keywords(event_data.get('titre', '') + ' ' + event_data.get('description', ''))
        categories = {
            'technologie': ['tech', 'numérique', 'digital', 'ia', 'intelligence', 'artificielle', 'logiciel', 'web', 'code', 'programmation'],
            'business': ['business', 'entreprise', 'startup', 'finance', 'marketing', 'vente', 'stratégie', 'management'],
            'formation': ['formation', 'cours', 'apprentissage', 'éducation', 'stage', 'atelier', 'workshop'],
            'social': ['réseau', 'rencontre', 'social', 'communauté', 'partage', 'échange'],
            'culture': ['culture', 'art', 'musique', 'cinéma', 'théâtre', 'exposition', 'festival'],
            'sport': ['sport', 'compétition', 'course', 'match', 'tournoi', 'athlète'],
            'santé': ['santé', 'bien-être', 'médical', 'soin', 'thérapie', 'fitness']
        }
        for cat, kw_list in categories.items():
            if any(k in keywords for k in kw_list):
                return cat
        return 'divers'

    # -----------------------------
    # Génération de prompt structuré
    # -----------------------------
    def build_structured_prompt(self, event_data: Dict[str, Any], context_events: Optional[List[Dict]] = None) -> str:
        """Construit un prompt complet pour l’IA avec contexte et recommandations."""
        cleaned_title = self.clean_text(event_data.get('titre', ''))
        cleaned_desc = self.clean_text(event_data.get('description', ''))
        keywords = self.extract_keywords(event_data.get('titre', '') + ' ' + event_data.get('description', ''))
        category = self.categorize_event(event_data)

        # Gestion dates
        date_info = ""
        if event_data.get('date_debut'):
            dt = event_data['date_debut']
            if isinstance(dt, datetime):
                dt = timezone.localtime(dt)
            date_info = f"Date: {dt.strftime('%d/%m/%Y à %H:%M')}"

        # Prompt structuré
        prompt = f"""=== ÉVÉNEMENT ===
Catégorie: {category}
Titre: {event_data.get('titre', 'N/A')}
Lieu: {event_data.get('lieu', 'N/A')}
{date_info}
Capacité: {event_data.get('capacite_max', 'N/A')} personnes
Prix: {event_data.get('prix', 0)}€

=== DESCRIPTION ACTUELLE ===
{event_data.get('description', 'Aucune description')}

=== ANALYSE ===
Mots-clés principaux: {', '.join(keywords)}
Description nettoyée: {cleaned_desc}
Accroche recommandée: {cleaned_title[:50]}...

=== INSTRUCTIONS IA ===
Génère une description professionnelle, engageante et informative (150-300 mots). Inclure:
- Accroche basée sur la catégorie ({category})
- Lieu, date, capacités et prix si disponibles
- Bénéfices pour les participants
- Call-to-action clair
Éviter langage trop promotionnel ou promesses irréalistes."""

        # Contexte événements similaires
        if context_events:
            similar_events = [evt for evt in context_events if self.categorize_event(evt) == category][:3]
            if similar_events:
                prompt += "\n\n=== ÉVÉNEMENTS SIMILAIRES ==="
                for i, e in enumerate(similar_events, 1):
                    prompt += f"\n{i}. {e['titre']} | Lieu: {e.get('lieu', 'N/A')} | Date: {e.get('date_debut', 'N/A')}"

        return prompt

    # -----------------------------
    # Préparation batch
    # -----------------------------
    def prepare_batch_data(self, limit: int = 50) -> Dict[str, Any]:
        """Prépare un lot d’événements avec prompt structuré et catégories."""
        events = self.get_event_data()[:limit]
        prepared = {'total_events': len(events), 'categories': {}, 'events': []}

        for e in events:
            category = self.categorize_event(e)
            prepared['categories'][category] = prepared['categories'].get(category, 0) + 1
            prepared['events'].append({
                **e,
                'cleaned_title': self.clean_text(e['titre']),
                'cleaned_description': self.clean_text(e['description']),
                'keywords': self.extract_keywords(e['titre'] + ' ' + e['description']),
                'category': category,
                'structured_prompt': self.build_structured_prompt(e)
            })

        return prepared

# -----------------------------
# Fonctions utilitaires
# -----------------------------
def get_event_preparer() -> EventDataPreparer:
    """Retourne une instance du préparateur de données."""
    return EventDataPreparer()

def prepare_single_event(event_id: int) -> str:
    """Préparer un événement et générer le prompt structuré."""
    preparer = get_event_preparer()
    events = preparer.get_event_data(event_id)
    if not events:
        raise ValueError(f"Événement {event_id} introuvable")
    return preparer.build_structured_prompt(events[0])

def prepare_batch_events(limit: int = 50) -> Dict[str, Any]:
    """Préparer un lot d’événements pour analyse ou IA."""
    return get_event_preparer().prepare_batch_data(limit)