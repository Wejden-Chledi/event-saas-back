# apps/events/ai_service.py
import os
from openai import AzureOpenAI

_client = None

def get_openai_client():
    """Initialise le client Azure OpenAI paresseusement."""
    global _client
    if _client is None:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not api_key or not azure_endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY et AZURE_OPENAI_ENDPOINT doivent être définis")
        
        _client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version="2024-02-15-preview"
        )
    return _client

def generate_event_description(prompt_text: str) -> str:
    """Génère une description professionnelle d'événement via Azure OpenAI"""
    client = get_openai_client()
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "Tu es un assistant qui génère des descriptions d'événements professionnelles, complètes et engageantes."},
            {"role": "user", "content": prompt_text}
        ],
        temperature=0.7,
        max_tokens=400
    )

    return response.choices[0].message.content