# apps/users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # ---------------- JWT Authentication ----------------
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', views.logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ---------------- User Profile ----------------
    path('profile/', views.profile_view, name='profile'),

    # ---------------- Registration ----------------
    path('register/', views.register_view, name='register'),
    path('register-proprietaire/', views.register_proprietaire_view, name='register_proprietaire'),
    path('register-participant/', views.register_participant_view, name='register_participant'),
    path('update-proprietaire/', views.update_proprietaire_view, name='update_proprietaire'),
    path('update-abonnement/', views.update_abonnement_view, name='update_abonnement'),
]