from django import forms
from .models import Evaluation, Note, Utilisateur

#permet a l'enseignant de choisir une evaluation et de saisir les notes pour chaque eleve de la classe
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['valeur', 'commentaire', 'evaluation', 'eleve']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'evaluation' in self.data:
            evaluation_id = self.data.get('evaluation')
            try:
                # Si l'evaluation est valide filtrer les eleves associes à cette evaluation
                evaluation = Evaluation.objects.get(id=evaluation_id)
                self.fields['eleve'].queryset = Eleve.objects.filter(classe=evaluation.classe)
            except Evaluation.DoesNotExist:
                # Si l'evaluation n'existe pas ne rien afficher
                self.fields['eleve'].queryset = Eleve.objects.none()
        elif self.instance.pk:
            # Si l'instance du formulaire existe recuperer les eleves associes
            self.fields['eleve'].queryset = self.instance.evaluation.classe.eleve_set.all()
        else:
            # Si aucune evaluation n'est selectionnee ne montrer aucun eleve
            self.fields['eleve'].queryset = Eleve.objects.none()


class UtilisateurForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'role', 'password', 'image']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user