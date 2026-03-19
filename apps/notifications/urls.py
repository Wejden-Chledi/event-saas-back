# apps/notifications/urls.py
from django.urls import path
from .views import (
    NotificationCreateView,
    NotificationListView,
    NotificationDetailView,
    NotificationSendView,
)

urlpatterns = [
    # ================================
    # Notifications
    # ================================
    path('', NotificationCreateView.as_view(), name='notification-create'),
    path('mes-notifications/', NotificationListView.as_view(), name='notification-list'),
    path('<uuid:id>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<uuid:id>/envoyer/', NotificationSendView.as_view(), name='notification-send'),
]