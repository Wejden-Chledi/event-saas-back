# apps/assistant/services.py
import os
import json
import logging
from langdetect import detect, LangDetectException
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from apps.events.ai_service import get_openai_client
from apps.events.models import Evenement

logger = logging.getLogger(__name__)

# ==========================================
# 1. DÉTECTION DE LA LANGUE (RENFORCÉE)
# ==========================================
def detect_language(text):
    text_low = text.lower().strip()
    # Mots-clés anglais qui forcent le mode "EN"
    en_force = ["hi", "hello", "find", "search", "music", "events", "free", "details", "show"]
    
    if any(word in text_low.split() for word in en_force):
        return "en"
        
    try:
        lang = detect(text)
        return "fr" if lang.startswith("fr") else "en"
    except:
        return "en"

# ==========================================
# 2. LOGIQUE PRINCIPALE DU CHATBOT
# ==========================================
def get_chatbot_reply(user_query, chat_history=None):
    client = get_openai_client()
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    user_lang = detect_language(user_query)
    lang_label = "ENGLISH" if user_lang == "en" else "FRENCH"

    # --- PROMPT SYSTÈME ULTRA-DIRECT ---
    system_prompt = f"""
    ROLE: Eventora AI Assistant.
    STRICT LANGUAGE RULE: The user is speaking {lang_label}. 
    YOU MUST RESPOND IN {lang_label} ONLY.
    - If you find data in French, TRANSLATE IT to {lang_label}.
    - Do not say 'Voici' or 'Bonjour' if the language is ENGLISH.
    """

    messages = [{"role": "system", "content": system_prompt}]

    # Nettoyage historique (Max 2 pour éviter la pollution)
    if chat_history:
        for msg in chat_history[-2:]:
            messages.append(msg)

    messages.append({"role": "user", "content": user_query})

    # Définition des Tools
    tools = [{
        "type": "function",
        "function": {
            "name": "search_events",
            "description": "Find events in the database",
            "parameters": {
                "type": "object",
                "properties": {"query_term": {"type": "string"}}
            }
        }
    }]

    try:
        # PREMIER APPEL : Génération de la réponse
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            tools=tools,
            temperature=0
        )

        message = response.choices[0].message

        # GESTION DES OUTILS (Tools)
        if message.tool_calls:
            messages.append(message)
            for call in message.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                # Recherche en base (ton service existant)
                from .services import search_events_in_db
                result = search_events_in_db(query_term=args.get("query_term"))
                
                messages.append({
                    "role": "tool", 
                    "tool_call_id": call.id, 
                    "name": "search_events", 
                    "content": result
                })

            # INSTRUCTION DE TRADUCTION POST-OUTIL (Crucial)
            messages.append({
                "role": "system", 
                "content": f"The search results are above. Now, present them strictly in {lang_label}. Translate all French terms to {lang_label}."
            })

            final_call = client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=0
            )
            reply = final_call.choices[0].message.content
        else:
            reply = message.content

        # ==========================================
        # 3. LE FAIL-SAFE (LA DOUBLE VÉRIFICATION)
        # ==========================================
        # Si on attend de l'anglais mais que l'IA a glissé vers le français
        if user_lang == "en" and any(word in reply.lower() for word in ["voici", "événement", "bonjour", "disponible"]):
            logger.warning(" [LANGUAGE CORRECTION] AI failed to speak English. Forcing translation...")
            
            # Deuxième appel court pour forcer la traduction
            correction_response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "Translate the following text into English perfectly. Maintain the formatting."},
                    {"role": "user", "content": reply}
                ],
                temperature=0
            )
            return correction_response.choices[0].message.content

        return reply

    except Exception as e:
        logger.error(f"Error: {e}")
        return "I encountered an error." if user_lang == "en" else "Désolé, une erreur est survenue."