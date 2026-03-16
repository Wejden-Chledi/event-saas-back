# src/apps/proprietaire/admin.py

from django.contrib import admin
from django.utils import timezone
from .models import InformationOrganisation, Gestionnaire, DemandeAbonnement


@admin.register(InformationOrganisation)
class InformationOrganisationAdmin(admin.ModelAdmin):

    list_display = [
        'organisation',
        'siret',
        'forme_juridique',
        'nombre_employes',
        'date_mise_a_jour'
    ]

    list_filter = [
        'forme_juridique',
        'date_mise_a_jour'
    ]

    search_fields = [
        'organisation__nom',
        'siret'
    ]

    readonly_fields = [
        'date_mise_a_jour'
    ]


@admin.register(Gestionnaire)
class GestionnaireAdmin(admin.ModelAdmin):

    list_display = [
        'utilisateur_nom',
        'utilisateur_prenom',
        'utilisateur_email',
        'organisation',
        'departement',
        'actif',
        'date_creation'
    ]

    list_filter = [
        'actif',
        'departement',
        'organisation'
    ]

    search_fields = [
        'utilisateur__nom',
        'utilisateur__prenom',
        'utilisateur__email',
        'organisation__nom'
    ]

    readonly_fields = [
        'date_creation'
    ]

    # 🔹 Affichage utilisateur
    def utilisateur_nom(self, obj):
        return obj.utilisateur.nom if obj.utilisateur else ""
    utilisateur_nom.short_description = 'Nom'

    def utilisateur_prenom(self, obj):
        return obj.utilisateur.prenom if obj.utilisateur else ""
    utilisateur_prenom.short_description = 'Prénom'

    def utilisateur_email(self, obj):
        return obj.utilisateur.email if obj.utilisateur else ""
    utilisateur_email.short_description = 'Email'

    fieldsets = (
        ('Utilisateur', {
            'fields': ('utilisateur', 'organisation')
        }),

        ('Organisation interne', {
            'fields': ('departement',)
        }),

        ('Permissions', {
            'fields': (
                'peut_gerer_evenements',
                'peut_gerer_finances',
                'peut_gerer_personnel',
                'peut_voir_rapports'
            )
        }),

        ('Statut', {
            'fields': ('actif', 'date_creation')
        }),
    )


@admin.register(DemandeAbonnement)
class DemandeAbonnementAdmin(admin.ModelAdmin):

    list_display = [
        'organisation',
        'type_demande',
        'montant_propose',
        'statut',
        'date_demande',
        'date_traitement'
    ]

    list_filter = [
        'type_demande',
        'statut',
        'date_demande'
    ]

    search_fields = [
        'organisation__nom',
        'raison'
    ]

    readonly_fields = [
        'date_demande'
    ]

    actions = [
        'approuver_demande',
        'refuser_demande'
    ]

    # 🔹 Action approuver
    def approuver_demande(self, request, queryset):

        for demande in queryset:
            demande.statut = 'approuve'
            demande.date_traitement = timezone.now()
            demande.save()

        self.message_user(
            request,
            f"{queryset.count()} demande(s) approuvée(s)"
        )

    approuver_demande.short_description = "Approuver les demandes sélectionnées"

    # 🔹 Action refuser
    def refuser_demande(self, request, queryset):

        for demande in queryset:
            demande.statut = 'refuse'
            demande.date_traitement = timezone.now()
            demande.save()

        self.message_user(
            request,
            f"{queryset.count()} demande(s) refusée(s)"
        )

    refuser_demande.short_description = "Refuser les demandes sélectionnées"