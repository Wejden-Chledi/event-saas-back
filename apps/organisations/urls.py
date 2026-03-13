from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OrganisationViewSet, AbonnementViewSet

router = DefaultRouter()
router.register(r'organisations', OrganisationViewSet)
router.register(r'abonnements', AbonnementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
