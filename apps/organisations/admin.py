# apps/organisations/admin.py
from django.contrib import admin
from .models import Organisation, Abonnement

# ===============================
# ADMIN ABONNEMENT
# ===============================
@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    # Corrigé : noms exacts des champs du modèle
    list_display = ['plan', 'statut', 'montant', 'date_debut', 'date_fin', 'date_creation']
    list_filter = ['plan', 'statut', 'date_creation']
    search_fields = ['plan', 'statut']
    readonly_fields = ['date_creation']

# ===============================
# ADMIN ORGANISATION
# ===============================
@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    # Corrigé : noms exacts des champs du modèle
    list_display = ['nom', 'secteur', 'email_contact', 'proprietaire', 'abonnement', 'date_creation']
    list_filter = ['secteur', 'abonnement', 'date_creation']
    search_fields = ['nom', 'email_contact', 'proprietaire__email']
    readonly_fields = ['date_creation']