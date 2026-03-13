import os
from openai import AzureOpenAI

# Client initialisé paresseusement pour éviter les erreurs au démarrage
_client = None

def get_openai_client():
    """Initialiser et retourner le client Azure OpenAI de manière paresseuse"""
    global _client
    if _client is None:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not api_key or not azure_endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY et AZURE_OPENAI_ENDPOINT doivent être définis dans les variables d'environnement")
        
        _client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version="2024-02-15-preview"
        )
    return _client

def generate_event_description(title):
    """
    Génère une description professionnelle pour un événement en fonction de son titre
    """
    client = get_openai_client()
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "Tu es un assistant qui génère des descriptions professionnelles d'événements. Sois concis, informatif et engageant."},
            {"role": "user", "content": f"Créer une description pour un événement intitulé : {title}"}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content
