from django.urls import path
from . import views



urlpatterns = [
    path("evenements/", views.EvenementViewSet.as_view({"get": "list","post": "create" }), name="evenement-list"),
    path("evenements/<int:pk>/", views.EvenementViewSet.as_view({"get": "retrieve","put": "update","patch": "partial_update","delete": "destroy"}), name="evenement-detail"),
    path("evenements/<int:pk>/participants/", views.participants_event, name="participants-evenement"),
    
    path("staff/", views.StaffViewSet.as_view({"get": "list", "post": "create"}), name="staff-list"),
    path("staff/<uuid:pk>/", views.StaffViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="staff-detail"),
    path("staff/<uuid:pk>/assigner-evenement/", views.StaffViewSet.as_view({"post": "assigner_evenement"}), name="staff-assigner-evenement"),

    path("billets/", views.BilletViewSet.as_view({"get": "list"}), name="billet-list"),
    path("billets/<int:pk>/", views.BilletViewSet.as_view({"get": "retrieve"}), name="billet-detail"),
    path("billets/<int:pk>/utiliser/", views.BilletViewSet.as_view({"post": "utiliser"}), name="billet-utiliser"),

    path("register-event/", views.register_event_participant, name="register-event"),
    path("mes-inscriptions/", views.mes_inscriptions, name="mes-inscriptions"),
    path("mon-billet/<str:inscription_id>/", views.mon_billet, name="mon-billet"),
    path("telecharger-billet-pdf/<uuid:inscription_id>/", views.telecharger_billet_pdf, name="telecharger_billet_pdf"),

    path("public-events/", views.public_events, name="public-events"),
    path("debug/profile/", views.debug_user_profile, name="debug-profile"),
    path("ia/generate-description/", views.generate_event_description, name="generate-description")
]