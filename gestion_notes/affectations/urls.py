from django.urls import path
from . import views

urlpatterns = [
    path('administrateur/affecter-enseignant/', views.affecter_enseignant, name='affecter_enseignant'),
    path('administrateur/affecter-eleve/', views.affecter_eleve, name='affecter_eleve'),
]


