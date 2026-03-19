# apps/organisations/urls.py

from django.urls import path
from .views import *

urlpatterns = [

    # ==============================
    # ORGANISATION
    # ==============================
    path("create/", create_organisation_view),
    path("me/", get_my_organisation_view),
    path("update/", update_organisation_view),
    path("delete/", delete_organisation_view),

    # ==============================
    # ABONNEMENT
    # ==============================
    path("abonnement/", get_abonnement_view),
    path("abonnement/update/", update_abonnement_view),
]