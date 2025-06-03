from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('administrateur/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('enseignant/dashboard/', views.enseignant_dashboard, name='enseignant_dashboard'),
    path('eleve/dashboard/', views.eleve_dashboard, name='eleve_dashboard'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('administrateur/utilisateurs/', views.gestion_utilisateurs, name='gestion_utilisateurs'),
    path('administrateur/utilisateurs/creer/', views.creer_utilisateur, name='creer_utilisateur'),
    path('administrateur/utilisateurs/modifier/<int:utilisateur_id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('administrateur/utilisateurs/supprimer/<int:utilisateur_id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
]