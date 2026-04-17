import pytest
import json
from apps.assistant.services import search_events_in_db

@pytest.mark.django_db
@pytest.mark.parametrize("query, expected_title", [
    ("React", "Conférence React"),
    ("Paris", "Conférence React"),  # C'est ici que ça échoue actuellement
    ("DJANGO", "DJANGO WORKSHOP"),
    ("Lyon", "DJANGO WORKSHOP"),   # C'est ici aussi
])
def test_search_service_logic(create_event, query, expected_title):
    # 1. On crée les données proprement via les fixtures
    create_event("Conférence React", lieu="Paris")
    create_event("DJANGO WORKSHOP", lieu="Lyon")

    # 2. On appelle le service
    raw_results = search_events_in_db(query)
    
    # 3. On vérifie si c'est du JSON ou un message d'erreur
    try:
        results = json.loads(raw_results)
        # Si c'est du JSON, on vérifie le contenu
        assert any(expected_title.lower() in event['title'].lower() for event in results)
    except json.JSONDecodeError:
        # Si c'est du texte, le test échoue avec un message clair pour t'aider à débugger
        pytest.fail(f"Le service n'a pas trouvé '{query}'. Message reçu: {raw_results}")