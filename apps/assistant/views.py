# apps/assistant/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import get_chatbot_reply

class ChatbotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_query = request.data.get("message")
        history = request.data.get("history", []) # Le frontend enverra l'historique
        
        reply = get_chatbot_reply(user_query, history)
        
        return Response({"reply": reply})