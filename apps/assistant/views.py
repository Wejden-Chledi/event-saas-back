# apps/assistant/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import get_chatbot_reply


class ChatbotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_query = request.data.get("message")
        history = request.data.get("history", [])[-10:]

        if not user_query:
            return Response({"error": "Message is required"}, status=400)

        reply = get_chatbot_reply(user_query, history)

        return Response({"reply": reply})

        #Quels sont les événements prévus pour le mois prochain à Paris ?
        #Est-ce que l'événement 'Conférence React' accepte les remboursements ?
        #Où se déroule l'atelier de demain et à quelle heure commence-t-il ?
        #Y a-t-il des tarifs réduits ou des événements gratuits en ce moment ?
        #Je n'arrive pas à payer avec ma carte, quelles sont les étapes ?
        
        """🔹 Questions simples
Quels sont les événements disponibles ?
Montre-moi les événements à Paris
Y a-t-il des événements aujourd’hui ?
Quels événements sont gratuits ?
Donne-moi les événements avec prix inférieur à 20€
🔹 Questions avec détails
Donne-moi les détails de l’événement "Concert Jazz"
Où se déroule cet événement ?
Quelle est la capacité de cet événement ?
Combien de places restent disponibles ?
Cet événement est-il complet ?
🔹 Questions avancées
Quels événements commencent cette semaine ?
Montre-moi les événements à Rome avec places disponibles
Quels événements sont déjà complets ?
Donne-moi les événements avec description contenant "musique"
Quel est l’événement le moins cher ?
🇬🇧 Tests in English
🔹 Basic questions
What events are available?
Show me events in Rome
Are there any events today?
Which events are free?
Show events under 50€
🔹 Detailed questions
Give me details about the event "Tech Conference"
Where is this event located?
What is the capacity of this event?
How many seats are left?
Is this event full?
🔹 Advanced queries
Which events are happening this week?
Show events in Milan with available seats
Which events are already full?
Find events related to music
What is the cheapest event?"""