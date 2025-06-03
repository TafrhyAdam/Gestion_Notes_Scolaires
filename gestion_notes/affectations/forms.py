from django import forms
from alertes.models import Utilisateur
from evaluations.models import Matiere, Classe  
from .models import EleveClasse


# formulaires pour affecter 
class AffectationForm(forms.Form):
    matiere = forms.ModelChoiceField(queryset=Matiere.objects.all())
    enseignant = forms.ModelChoiceField(queryset=Utilisateur.objects.filter(role='enseignant'))

class AffectationEleveForm(forms.Form):
    eleve = forms.ModelChoiceField(queryset=Utilisateur.objects.filter(role='eleve'))
    classe = forms.ModelChoiceField(queryset=Classe.objects.all())
