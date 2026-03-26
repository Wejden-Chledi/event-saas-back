# apps/notifications/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    """Lister les notifications de l'utilisateur connecté"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(destinataire=self.request.user).order_by('-date_creation')

class NotificationDetailView(generics.RetrieveAPIView):
    """Détail d'une notification (doit appartenir à l'utilisateur)"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(destinataire=self.request.user)

class NotificationSendView(APIView):
    """Déclencher l'envoi manuel"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            # Sécurité : on ne peut envoyer que ses propres notifications
            notification = Notification.objects.get(pk=pk, destinataire=request.user)
            success = notification.envoyer()
            
            if success:
                return Response({"detail": "Notification envoyée avec succès"})
            return Response({"detail": "L'envoi a échoué"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Notification.DoesNotExist:
            return Response({"detail": "Notification non trouvée"}, status=status.HTTP_404_NOT_FOUND)