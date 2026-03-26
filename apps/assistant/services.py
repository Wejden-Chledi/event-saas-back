# apps/assistant/services.py
import os
from apps.events.ai_service import get_openai_client
from apps.events.models import Evenement

def get_chatbot_reply(user_query, chat_history=None):
    client = get_openai_client()
    
    # 1. Récupération du contexte (RAG simple)
    # On récupère les 5 prochains événements pour informer l'IA
    events = Evenement.objects.filter(statut='publie').order_by('date_debut')[:5]
    events_ctx = "\n".join([f"- {e.titre}: le {e.date_debut} à {e.lieu}. Prix: {e.prix}€" for e in events])

    # 2. Configuration du System Prompt
    messages = [
        {
            "role": "system", 
            "content": f"""Tu es l'assistant de 'Event SaaS'. 
            Réponds aux questions des participants sur la plateforme ou les événements suivants :
            {events_ctx}
            Si une question ne concerne pas ces sujets, reste poli mais redirige vers le support."""
        }
    ]

    # 3. Ajout de l'historique (si fourni par React)
    if chat_history:
        messages.extend(chat_history)

    # 4. Ajout du message actuel
    messages.append({"role": "user", "content": user_query})

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=messages,
        temperature=0.5
    )
    return response.choices[0].message.content