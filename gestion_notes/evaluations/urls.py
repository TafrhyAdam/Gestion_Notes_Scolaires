from django.urls import path
from . import views



urlpatterns = [
    path('saisie_notes/', views.saisie_notes, name='saisie_notes'),
    path('notes/', views.consulter_notes, name='consulter_notes'),
    path('enseignant/stats/', views.enseignant_stats, name='enseignant_stats'),
    path('administrateur/stats/', views.admin_stats, name='admin_stats'),
]
