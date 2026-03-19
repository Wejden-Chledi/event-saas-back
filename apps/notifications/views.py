# apps/notifications/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


# ================================
# Créer une notification
# ================================
class NotificationCreateView(generics.CreateAPIView):
    """
    Permet de créer une notification (email, SMS, push).
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]


# ================================
# Lister les notifications
# ================================
class NotificationListView(generics.ListAPIView):
    """
    Affiche toutes les notifications de l'utilisateur connecté.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(destinataire=self.request.user).order_by('-date_creation')


# ================================
# Détails d'une notification
# ================================
class NotificationDetailView(generics.RetrieveAPIView):
    """
    Récupère le détail d'une notification spécifique.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"


# ================================
# Envoyer une notification
# ================================
class NotificationSendView(APIView):
    """
    Déclenche l'envoi réel de la notification (simulation ou réel via SMTP/Push/SMS).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            notification = Notification.objects.get(id=id)
            notification.envoyer()  # appelle la méthode envoyer() du modèle
            return Response({"detail": "Notification envoyée"}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"detail": "Notification non trouvée"}, status=status.HTTP_404_NOT_FOUND)