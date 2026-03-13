from django.contrib import admin
from .models import Organisation, Abonnement


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'secteur', 'emailContact', 'proprietaire', 'statutAbonnement', 'dateCreation']
    list_filter = ['secteur', 'statutAbonnement', 'dateCreation']
    search_fields = ['nom', 'emailContact', 'proprietaire__email']
    readonly_fields = ['dateCreation']


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ['type', 'statut', 'montant', 'dateDebut', 'dateFin', 'dateCreation']
    list_filter = ['type', 'statut', 'dateCreation']
    search_fields = ['type', 'statut']
    readonly_fields = ['dateCreation']
