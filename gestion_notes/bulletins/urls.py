from django.urls import path
from . import views

urlpatterns = [
    path('', views.page_resultats_bulletins, name='page_resultats_bulletins'),
    path('generer_bulletins_multiple/', views.generer_bulletins_multiple, name='generer_bulletins_multiple'),
    path('eleve/bulletins/', views.bulletin_eleve, name='bulletin_eleve'),
    path('parent/bulletins/', views.bulletins_parent, name='bulletins_parent'),
    path('rendre_bulletins_disponibles/', views.rendre_bulletins_disponibles, name='rendre_bulletins_disponibles'),
    path('supprimer_bulletin/<int:bulletin_id>/', views.supprimer_bulletin, name='supprimer_bulletin'),
]