# apps/feedback/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedbackViewSet, RapportIAViewSet

router = DefaultRouter()
router.register(r'avis', FeedbackViewSet, basename='feedback')
router.register(r'rapports-ia', RapportIAViewSet, basename='rapport-ia')

urlpatterns = [
    path('', include(router.urls)),
]