# ============================================================================
# Fichier : apps/assistant/views.py
#
# Ce fichier contient les vues API liées à l'assistant intelligent Eventora.
#
# Il définit :
#
#   - ChatbotView :
#       Endpoint permettant aux utilisateurs authentifiés d'envoyer
#       des questions au chatbot et de recevoir une réponse générée
#       par le service IA.
#
# Cette vue assure l'interaction entre le frontend et le service chatbot
# basé sur Azure OpenAI.
# ============================================================================


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services import get_chatbot_reply


# ============================================================================
# VUE CHATBOT
# ============================================================================

class ChatbotView(APIView):
    """
    Vue API permettant de communiquer avec l'assistant intelligent.

    L'utilisateur envoie :
        - Un message contenant sa question.
        - Un historique optionnel des conversations précédentes.

    Le service chatbot analyse la demande et retourne une réponse
    adaptée selon le contexte et la langue détectée.
    """

    # Seuls les utilisateurs connectés peuvent utiliser l'assistant
    permission_classes = [IsAuthenticated]


    def post(self, request):
        """
        Traite une requête utilisateur envoyée au chatbot.

        Étapes :
            1. Récupération du message utilisateur.
            2. Récupération des derniers échanges pour conserver le contexte.
            3. Appel du service IA.
            4. Retour de la réponse générée.
        """

        # Récupération de la question envoyée par le participant
        user_query = request.data.get("message")


        # Conservation des 10 derniers messages pour limiter la taille du contexte
        history = request.data.get("history", [])[-10:]


        # Vérification de la présence d'un message
        if not user_query:
            return Response(
                {"error": "Message is required"},
                status=400
            )


        # Appel du service chatbot basé sur Azure OpenAI
        reply = get_chatbot_reply(
            user_query,
            history
        )


        # Retour de la réponse au frontend
        return Response({
            "reply": reply
        })


# ============================================================================
# EXEMPLES DE QUESTIONS TESTEES AVEC LE CHATBOT
#
# Ces exemples permettent de valider les capacités de recherche,
# compréhension du langage naturel et interaction avec les données
# des événements.
#
# Questions générales :
#
#   - Quels sont les événements disponibles ?
#   - Montre-moi les événements à Paris.
#   - Y a-t-il des événements aujourd’hui ?
#   - Quels événements sont gratuits ?
#   - Donne-moi les événements avec prix inférieur à 20€.
#
# Questions détaillées :
#
#   - Donne-moi les détails de l’événement "Concert Jazz".
#   - Où se déroule cet événement ?
#   - Quelle est la capacité de cet événement ?
#   - Combien de places restent disponibles ?
#   - Cet événement est-il complet ?
#
# Questions avancées :
#
#   - Quels événements commencent cette semaine ?
#   - Montre-moi les événements à Rome avec places disponibles.
#   - Quels événements sont déjà complets ?
#   - Donne-moi les événements contenant "musique".
#   - Quel est l’événement le moins cher ?
#
# Tests en anglais :
#
#   - What events are available?
#   - Show me events in Rome.
#   - Are there any events today?
#   - Which events are free?
#   - Show events under 50€.
#   - Give me details about the event "Tech Conference".
#   - Where is this event located?
#   - What is the capacity of this event?
#   - How many seats are left?
#   - Is this event full?
#   - Which events are happening this week?
#   - Show events in Milan with available seats.
#   - Which events are already full?
#   - Find events related to music.
#   - What is the cheapest event?
# ============================================================================