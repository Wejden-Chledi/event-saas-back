# apps/events/views/debug_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def debug_user_profile(request):
    """
    Retourne un profil utilisateur fictif pour debug
    """
    # tu peux remplacer par de vrais objets si tu veux tester
    data = {
        "id": 1,
        "nom": "Test",
        "email": "test@example.com",
        "role": "participant"
    }
    return Response(data)