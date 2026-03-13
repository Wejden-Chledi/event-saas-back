import re
from datetime import datetime
from typing import Dict, List, Optional
from .models import Evenement

class EventDataPreparer:
    """Service pour préparer et nettoyer les données événements pour l'IA"""
    
    def __init__(self):
        self.stop_words = [
            'le', 'la', 'les', 'de', 'des', 'du', 'au', 'aux', 'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car',
            'un', 'une', 'dans', 'sur', 'sous', 'avec', 'pour', 'par', 'vers', 'entre', 'chez', 'pendant'
        ]
    
    def get_event_data(self, event_id: Optional[int] = None) -> List[Dict]:
        """
        Récupérer les données événements depuis la base de données
        """
        if event_id:
            events = Evenement.objects.filter(id=event_id)
        else:
            events = Evenement.objects.all()
        
        return [
            {
                'id': event.id,
                'titre': event.titre,
                'description': event.description,
                'lieu': event.lieu,
                'statut': event.statut,
                'date_debut': event.dateDebut,
                'date_fin': event.dateFin,
                'capacite_max': event.capaciteMax,
                'prix': float(event.prix),
                'organisation': event.organisation.nom if event.organisation else None,
                'createur': f"{event.createur.nom} {event.createur.prenom}" if event.createur else None
            }
            for event in events
        ]
    
    def clean_text(self, text: str) -> str:
        """
        Nettoyer un texte : suppression des caractères spéciaux, normalisation
        """
        if not text:
            return ""
        
        # Conversion en minuscules
        text = text.lower().strip()
        
        # Suppression des caractères spéciaux sauf espaces et accents
        text = re.sub(r'[^\w\sàáâäãåçèéêëìíîïñòóôöõùúûüýÿ]', ' ', text)
        
        # Suppression des espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Suppression des stop words
        words = text.split()
        words = [word for word in words if word not in self.stop_words]
        
        return ' '.join(words)
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        Extraire les mots-clés les plus pertinents d'un texte
        """
        cleaned_text = self.clean_text(text)
        words = cleaned_text.split()
        
        # Compter la fréquence des mots
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Ignorer les mots trop courts
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Trier par fréquence et retourner les top mots-clés
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def categorize_event(self, event_data: Dict) -> str:
        """
        Catégoriser automatiquement un événement basé sur son titre et description
        """
        title_keywords = self.extract_keywords(event_data['titre'])
        desc_keywords = self.extract_keywords(event_data['description'])
        all_keywords = title_keywords + desc_keywords
        
        # Catégories basées sur les mots-clés
        categories = {
            'technologie': ['tech', 'numérique', 'digital', 'ia', 'intelligence', 'artificielle', 'logiciel', 'application', 'web', 'code', 'programmation'],
            'business': ['business', 'entreprise', 'startup', 'finance', 'marketing', 'vente', 'stratégie', 'management'],
            'formation': ['formation', 'cours', 'apprentissage', 'éducation', 'stage', 'atelier', 'workshop'],
            'social': ['réseau', 'rencontre', 'social', 'communauté', 'partage', 'échange'],
            'culture': ['culture', 'art', 'musique', 'cinéma', 'théâtre', 'exposition', 'festival'],
            'sport': ['sport', 'compétition', 'course', 'match', 'tournoi', 'athlète'],
            'santé': ['santé', 'bien-être', 'médical', 'soin', 'thérapie', 'fitness']
        }
        
        for category, keywords in categories.items():
            if any(keyword in all_keywords for keyword in keywords):
                return category
        
        return 'divers'
    
    def build_structured_prompt(self, event_data: Dict, context_events: Optional[List[Dict]] = None) -> str:
        """
        Construire un prompt structuré pour l'IA basé sur les données événement
        """
        # Nettoyage et extraction des données
        cleaned_title = self.clean_text(event_data['titre'])
        cleaned_desc = self.clean_text(event_data['description'])
        keywords = self.extract_keywords(event_data['titre'] + ' ' + event_data['description'])
        category = self.categorize_event(event_data)
        
        # Informations temporelles
        date_debut = event_data['date_debut']
        date_info = ""
        if date_debut:
            date_info = f"Date: {date_debut.strftime('%d/%m/%Y à %H:%M')}"
        
        # Construction du prompt structuré
        prompt = f"""=== CONTEXTE ÉVÉNEMENT ===
Catégorie: {category}
Titre original: {event_data['titre']}
Titre nettoyé: {cleaned_title}
Lieu: {event_data.get('lieu', 'Non spécifié')}
{date_info}
Capacité: {event_data.get('capacite_max', 'Non spécifiée')} personnes
Prix: {event_data.get('prix', 0)}€

=== DESCRIPTION ACTUELLE ===
{event_data.get('description', 'Aucune description')}

=== ANALYSE SÉMANTIQUE ===
Mots-clés principaux: {', '.join(keywords)}
Description nettoyée: {cleaned_desc}"""

        # Ajout du contexte d'autres événements similaires si disponible
        if context_events:
            similar_events = [evt for evt in context_events if self.categorize_event(evt) == category][:3]
            if similar_events:
                prompt += f"""

=== ÉVÉNEMENTS SIMILAIRES RÉCENTS ==="""
                for i, similar_event in enumerate(similar_events, 1):
                    prompt += f"""
{i}. {similar_event['titre']}
   Lieu: {similar_event.get('lieu', 'N/A')}
   Date: {similar_event.get('date_debut', 'N/A')}
   Description: {similar_event.get('description', 'N/A')[:100]}..."""

        # Instructions pour l'IA
        prompt += f"""

=== INSTRUCTIONS POUR L'IA ===
Génère une description professionnelle et engageante pour cet événement en suivant ces directives:
1. Style: Professionnel mais accessible
2. Ton: Engageant et informatif
3. Longueur: 150-300 mots
4. Éléments à inclure:
   - Accroche percutante basée sur la catégorie ({category})
   - Informations pratiques (lieu, date si disponibles)
   - Bénéfices pour les participants
   - Call-to-action clair
5. Éviter: Langage trop promotionnel, promesses irréalistes

=== SORTIE ATTENDUE ===
Description optimisée:"""

        return prompt
    
    def prepare_batch_data(self, limit: int = 50) -> Dict:
        """
        Préparer un lot de données pour analyse batch
        """
        events = self.get_event_data()[:limit]
        
        prepared_data = {
            'total_events': len(events),
            'categories': {},
            'events': []
        }
        
        for event in events:
            category = self.categorize_event(event)
            prepared_data['categories'][category] = prepared_data['categories'].get(category, 0) + 1
            
            prepared_event = {
                **event,
                'cleaned_title': self.clean_text(event['titre']),
                'cleaned_description': self.clean_text(event['description']),
                'keywords': self.extract_keywords(event['titre'] + ' ' + event['description']),
                'category': category,
                'structured_prompt': self.build_structured_prompt(event)
            }
            prepared_data['events'].append(prepared_event)
        
        return prepared_data

# Fonctions utilitaires pour l'exportation
def get_event_preparer():
    """Retourne une instance du préparateur de données"""
    return EventDataPreparer()

def prepare_single_event(event_id: int) -> str:
    """Préparer un seul événement et retourner le prompt structuré"""
    preparer = get_event_preparer()
    events = preparer.get_event_data(event_id)
    
    if not events:
        raise ValueError(f"Événement {event_id} non trouvé")
    
    return preparer.build_structured_prompt(events[0])

def prepare_batch_events(limit: int = 50) -> Dict:
    """Préparer un lot d'événements pour analyse"""
    preparer = get_event_preparer()
    return preparer.prepare_batch_data(limit)
