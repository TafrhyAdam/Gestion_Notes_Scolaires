from django.urls import path
from . import views
from alertes import views

urlpatterns = [
    path('alerte/<int:alerte_id>/lue/', views.marquer_alerte_lue, name='marquer_alerte_lue'),
]

