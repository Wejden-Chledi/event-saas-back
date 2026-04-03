# apps/assistant/services.py
import os
import json
import logging
from langdetect import detect
from django.db.models import Q

from apps.events.ai_service import get_openai_client
from apps.events.models import Evenement

logger = logging.getLogger(__name__)

# ==========================================
# 1. RÉCUPÉRATION DES DONNÉES (DB)
# ==========================================
def search_events_in_db(query_term=None):
    try:
        events = Evenement.objects.all()
        if query_term:
            events = events.filter(
                Q(titre__icontains=query_term) | 
                Q(description__icontains=query_term)
            ).distinct()

        if not events.exists():
            return "Aucun événement trouvé / No events found."

        results = []
        for e in events:
            # On calcule les places restantes ici pour aider l'IA
            total = getattr(e, 'capacite', 0)
            pris = getattr(e, 'places_reservees', 0) # Adaptez selon votre champ réel
            dispo = total - pris
            
            results.append({
                "title": e.titre,
                "date": e.date_debut.strftime("%d/%m/%Y") if e.date_debut else "N/A",
                "location": e.lieu,
                "capacity_total": total,
                "capacity_taken": pris,
                "available_slots": dispo,
                "description": e.description
            })
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur DB: {e}")
        return "Erreur technique."

# ==========================================
# 2. DÉTECTION DE LANGUE (ULTRA-STRICTE)
# ==========================================
def detect_language(text):
    text_low = text.lower().strip()
    # On force l'anglais sur des mots-clés typiques
    en_keywords = ["is", "are", "there", "any", "how", "many", "available", "show", "event"]
    if any(word in text_low.split() for word in en_keywords):
        return "en"
    try:
        lang = detect(text)
        return "fr" if lang.startswith("fr") else "en"
    except:
        return "fr" # Par défaut en français si on est pas sûr

# ==========================================
# 3. SERVICE CHATBOT
# ==========================================
def get_chatbot_reply(user_query, chat_history=None):
    client = get_openai_client()
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    # 1. Détecter la langue de la question actuelle
    user_lang = detect_language(user_query)
    lang_name = "FRENCH" if user_lang == "fr" else "ENGLISH"

    # --- SYSTEM PROMPT : LE VERROU ---
    system_prompt = f"""
    ROLE: Eventora Assistant.
    CURRENT LANGUAGE: {lang_name}.
    STRICT RULE: You must reply ONLY in {lang_name}. 
    - If the user asks in French, reply in French. 
    - If the user asks in English, reply in English.
    - Never switch language during the conversation. 
    - Translate any data found in the database to {lang_name}.
    """

    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history:
        # On injecte l'historique (max 5)
        messages.extend(chat_history[-5:])

    messages.append({"role": "user", "content": user_query})

    tools = [{
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "Get event details and availability from database",
            "parameters": {
                "type": "object",
                "properties": {"query_term": {"type": "string"}}
            }
        }
    }]

    try:
        # APPEL 1 : Analyse de la question
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            tools=tools,
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

            # --- LE SECRET : RÉ-INSTRUCTION FINALE ---
            # On rappelle la langue juste AVANT de générer la réponse finale
            messages.append({
                "role": "system", 
                "content": f"REMINDER: Your response must be 100% in {lang_name}. Do not use any other language."
            })

            final_response = client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=0.3 # Un peu de créativité pour la fluidité
            )
            return final_response.choices[0].message.content
        
        return message.content

    except Exception as e:
        logger.error(f"Chatbot Error: {e}")
        return "Désolé, j'ai rencontré un problème." if user_lang == "fr" else "Sorry, I encountered an error."