# ============================================================================
# Fichier : apps/assistant/services.py
# ============================================================================

import os
import json
import logging
from langdetect import detect
from django.db.models import Q
from apps.events.ai_service import get_openai_client
from apps.events.models import Evenement

logger = logging.getLogger(__name__)

def search_events_in_db(query_term=None):
    """Recherche les événements en base de données."""
    try:
        events = Evenement.objects.all()
        if query_term:
            events = events.filter(
                Q(titre__icontains=query_term) |
                Q(description__icontains=query_term) |
                Q(lieu__icontains=query_term)
            ).distinct()
        if not events.exists():
            return "Aucun événement trouvé / No events found."
        results = []
        for e in events:
            total = getattr(e, 'capacite_max', 0)
            pris = getattr(e, 'places_reservees', 0)
            dispo = max(0, total - pris)
            results.append({
                "title": e.titre,
                "date": e.date_debut.strftime("%d/%m/%Y") if e.date_debut else "N/A",
                "location": e.lieu,
                "capacity_total": total,
                "capacity_taken": pris,
                "available_slots": dispo,
                "description": e.description or ""
            })
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur DB dans search_events_in_db: {e}")
        return "Erreur technique lors de la recherche."

def detect_language(text):
    """Détecte la langue utilisée par l'utilisateur."""
    text_low = text.lower().strip()
    en_keywords = ["is", "are", "there", "any", "how", "many", "available", "show", "event", "where"]
    if any(word in text_low.split() for word in en_keywords):
        return "en"
    try:
        lang = detect(text)
        return "fr" if lang.startswith("fr") else "en"
    except:
        return "fr"

def get_chatbot_reply(user_query, chat_history=None):
    """Orchestre la réponse du chatbot via Azure OpenAI."""
    client = get_openai_client()
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    user_lang = detect_language(user_query)
    lang_name = "FRENCH" if user_lang == "fr" else "ENGLISH"
    
    system_prompt = f"""
    ROLE: Eventora Assistant.
    CURRENT LANGUAGE: {lang_name}.
    STRICT RULE: You must reply ONLY in {lang_name}. 
    - Translate any data found in the database to {lang_name}.
    - Be concise and helpful.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        messages.extend(chat_history[-5:])
    messages.append({"role": "user", "content": user_query})
    
    tools = [{
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "Get event details and availability from database",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_term": {
                        "type": "string",
                        "description": "The city or theme to search for"
                    }
                }
            }
        }
    }]
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0
        )
        message = response.choices[0].message
        
        if message.tool_calls:
            messages.append(message)
            for call in message.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                data = search_events_in_db(args.get("query_term"))
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": "get_events",
                    "content": data
                })
            messages.append({"role": "system", "content": f"REMINDER: Reply 100% in {lang_name}."})
            final_response = client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=0.3
            )
            return final_response.choices[0].message.content
            
        return message.content
    except Exception as e:
        logger.error(f"Chatbot Error: {e}")
        return "Désolé, j'ai rencontré un problème." if user_lang == "fr" else "Sorry, I encountered an error."