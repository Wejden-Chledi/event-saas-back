# ============================================================================
# Fichier : apps/events/data_prep_service.py
#
# Ce fichier contient le service de préparation des données événementielles
# avant leur envoi au modèle d'intelligence artificielle.
#
# Son rôle :
#
#   1. Nettoyer les textes des événements.
#   2. Supprimer les mots inutiles (stop words).
#   3. Déterminer automatiquement une catégorie d'événement.
#   4. Détecter la langue utilisée.
#   5. Construire un prompt structuré destiné à Azure OpenAI.
#
# Ce service est utilisé dans :
#
#       EvenementViewSet.generate_ai_desc()
#
# avant l'appel au service IA.
# ============================================================================
import re
from typing import (Dict,List,Optional,Any)
from .models import Evenement
from langdetect import (
    detect,
    DetectorFactory
)
DetectorFactory.seed = 0


# ============================================================================
# CLASSE : EventDataPreparer
# ============================================================================
#
# Cette classe regroupe toutes les fonctions nécessaires
# pour préparer les informations d'un événement
# avant leur utilisation par l'IA.
# ============================================================================
class EventDataPreparer:
    """
    Prépare et nettoie les données événements pour l'IA.
    """
    # ------------------------------------------------------------------------
    # Constructeur
    # ------------------------------------------------------------------------


    def __init__(self):


        # Liste des mots fréquents qui n'apportent
        # pas d'information importante pour l'analyse.
        self.stop_words = set([
            'le',
            'la',
            'les',

            'de',
            'des',
            'du',

            'au',
            'aux',

            'et',
            'ou',
            'mais',

            'donc',
            'or',
            'ni',
            'car',

            'un',
            'une',

            'dans',
            'sur',
            'sous',

            'avec',

            'pour',

            'par',

            'vers',

            'entre',

            'chez',

            'pendant'

        ])

    # =========================================================================
    # NETTOYAGE DU TEXTE
    # =========================================================================


    def clean_text(self, text: str) -> str:


        """
        Nettoie un texte avant son analyse.

        Opérations réalisées :

            - conversion en minuscules ;
            - suppression des caractères spéciaux ;
            - suppression des espaces multiples ;
            - suppression des stop words.
        """



        # Si aucun texte fourni,
        # retourner une chaîne vide.
        if not text:

            return ""

        # Conversion en minuscules
        # et suppression des espaces inutiles.
        text = text.lower().strip()

        # Suppression des caractères spéciaux.
        # Conservation :- lettres ;- chiffres ;- accents français.
        text = re.sub(
            r'[^\w\sàáâäãåçèéêëìíîïñòóôöõùúûüýÿ]',
            ' ',
            text
        )





        # Remplacement des espaces multiples
        # par un seul espace.
        text = re.sub(
            r'\s+',
            ' ',
            text
        )

        # Suppression des stop words.
        return ' '.join(
            [
                w
                for w in text.split()
                if w not in self.stop_words
            ]
        )

    # =========================================================================
    # CATEGORISATION AUTOMATIQUE
    # =========================================================================


    def categorize_event(
        self,
        event_data: Dict[str, Any]
    ) -> str:


        """
        Détermine automatiquement la catégorie
        d'un événement selon ses mots-clés.
        """



        # Fusion du titre et de la description.
        text = (
            f"{event_data.get('titre', '')} "
            f"{event_data.get('description', '')}"
        )



        # Nettoyage du texte.
        text = self.clean_text(text)




        # Conservation uniquement des mots
        # de plus de 3 caractères.
        keywords = [
            w
            for w in text.split()
            if len(w) > 3
        ]





        # Dictionnaire contenant les catégories
        # et leurs mots-clés associés.
        categories = {


            'technologie': [
                'tech',
                'numérique',
                'digital',
                'ia',
                'artificielle',
                'logiciel',
                'web',
                'code',
                'programmation'
            ],


            'business': [
                'business',
                'entreprise',
                'startup',
                'finance',
                'marketing',
                'vente',
                'stratégie',
                'management'
            ],


            'formation': [
                'formation',
                'cours',
                'atelier',
                'workshop',
                'éducation'
            ],


            'social': [
                'réseau',
                'rencontre',
                'social',
                'communauté',
                'partage'
            ],


            'culture': [
                'culture',
                'art',
                'musique',
                'cinéma',
                'théâtre',
                'exposition',
                'festival'
            ],


            'sport': [
                'sport',
                'compétition',
                'course',
                'match',
                'tournoi',
                'athlète'
            ],


            'santé': [
                'santé',
                'bien-être',
                'médical',
                'soin',
                'thérapie',
                'fitness'
            ]

        }





        # Recherche d'une correspondance
        # entre les mots du texte et les catégories.
        for cat, kw_list in categories.items():


            if any(
                k in keywords
                for k in kw_list
            ):

                return cat





        # Si aucune catégorie trouvée.
        return 'divers'







    # =========================================================================
    # DETECTION DE LA LANGUE
    # =========================================================================


    def detect_language(
        self,
        text: str
    ) -> str:


        """
        Détecte la langue du texte.

        Retour :
            fr      -> français
            en      -> anglais
            other   -> autre langue
        """



        try:


            # Analyse automatique de la langue.
            lang = detect(text)



            if lang.startswith('fr'):

                return 'fr'



            elif lang.startswith('en'):

                return 'en'



            return 'other'



        # Si la détection échoue.
        except:


            return 'other'








    # =========================================================================
    # CONSTRUCTION DU PROMPT IA
    # =========================================================================


    def build_structured_prompt(
        self,
        event_data: Dict[str, Any]
    ) -> str:


        """
        Construit un prompt structuré
        destiné au modèle Azure OpenAI.
        """



        # Détermination automatique
        # de la catégorie.
        category = self.categorize_event(
            event_data
        )



        # Récupération des informations événement.
        titre = event_data.get(
            'titre',
            ''
        )


        description = event_data.get(
            'description',
            ''
        )


        lieu = event_data.get(
            'lieu',
            ''
        )


        prix = event_data.get(
            'prix',
            0
        )


        capacite = event_data.get(
            'capacite_max',
            0
        )


        date_debut = event_data.get(
            'date_debut',
            'à définir'
        )


        date_fin = event_data.get(
            'date_fin',
            'à définir'
        )





        # Détection de la langue
        # basée sur le titre.
        langue = self.detect_language(
            titre
        )





        # ---------------------------------------------------------------------
        # Cas anglais
        # ---------------------------------------------------------------------

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





        # ---------------------------------------------------------------------
        # Cas français par défaut
        # ---------------------------------------------------------------------

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





        # Retour du prompt final
        # envoyé au modèle IA.
        return prompt