# apps/events/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from apps.events.views import (
    create_evenement_view,
    list_evenements_view,
    retrieve_evenement_view,
    update_evenement_view,
    delete_evenement_view,
    assign_staff_view,
    list_staff_assignes_view,
    generate_event_description,
    public_events
)

urlpatterns = [
    # CRUD événements pour gestionnaire
    path('gestionnaire/evenements/', list_evenements_view, name='list_evenements'),
    path('gestionnaire/evenements/create/', create_evenement_view, name='create_evenement'),
    path('gestionnaire/evenements/<int:evenement_id>/', retrieve_evenement_view, name='retrieve_evenement'),
    path('gestionnaire/evenements/<int:evenement_id>/update/', update_evenement_view, name='update_evenement'),
    path('gestionnaire/evenements/<int:evenement_id>/delete/', delete_evenement_view, name='delete_evenement'),

    # Assignation staff
    path('gestionnaire/assignations/', assign_staff_view, name='assign_staff'),
    path('gestionnaire/evenements/<int:evenement_id>/assignations/', list_staff_assignes_view, name='list_staff_assignes'),

    # IA
    path('ai/generate-description/', generate_event_description, name='generate_event_description'),

    # Public
    path('public/evenements/', public_events, name='public_events'),
]

# Support des suffixes (.json, .api, etc.)
urlpatterns = format_suffix_patterns(urlpatterns)