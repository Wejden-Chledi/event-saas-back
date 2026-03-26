# apps/users/permissions.py
from rest_framework.permissions import BasePermission

# Permissions par rôle + statut actif
class IsProprietaire(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "proprietaire" and
            request.user.statut == "actif"
        )

class IsGestionnaire(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "gestionnaire" and
            request.user.statut == "actif"
        )

class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "staff" and
            request.user.statut == "actif"
        )