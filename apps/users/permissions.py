# apps/users/permissions.py
from rest_framework.permissions import BasePermission

# ==============================================================================
# LES PERMISSIONS PAR RÔLE
# ==============================================================================
# Chaque classe ci-dessous hérite de 'BasePermission'.
# Elle renvoie True si l'accès est autorisé, False sinon.

class IsProprietaire(BasePermission):
    """
    Autorise l'accès uniquement si l'utilisateur est authentifié,
    possède le rôle 'proprietaire' et que son compte est 'actif'.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and        # Vérifie si l'user est connecté
            request.user.role == "proprietaire" and  # Vérifie le rôle
            request.user.statut == "actif"           # Vérifie si le compte n'est pas suspendu
        )

class IsGestionnaire(BasePermission):
    """
    Autorise l'accès uniquement pour les utilisateurs avec le rôle 'gestionnaire'
    et un statut 'actif'.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "gestionnaire" and
            request.user.statut == "actif"
        )

class IsStaff(BasePermission):
    """
    Autorise l'accès uniquement pour les utilisateurs avec le rôle 'staff'
    et un statut 'actif'.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "staff" and
            request.user.statut == "actif"
        )