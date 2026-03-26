# apps/notifications/urls.py
from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    NotificationSendView,
)

urlpatterns = [
    # Liste et détails pour le frontend de l'utilisateur
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    
    # Action d'envoi
    path('<int:pk>/envoyer/', NotificationSendView.as_view(), name='notification-send'),
]