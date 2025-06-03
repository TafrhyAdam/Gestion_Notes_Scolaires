from django.shortcuts import render, redirect
from .forms import AffectationForm, AffectationEleveForm
from django.contrib import messages
from .models import EleveClasse, Matiere, Utilisateur


#vues d’affectation
def affecter_enseignant(request):
    enseignants = Utilisateur.objects.filter(role='enseignant')
    matieres = Matiere.objects.all()
    selected_enseignant = None
    selected_matieres = []

    if request.method == 'POST':
        enseignant_id = request.POST.get('enseignant')
        selected_enseignant = enseignant_id
        selected_matieres = request.POST.getlist('matieres')
        if enseignant_id and selected_matieres:
            enseignant = Utilisateur.objects.get(id=enseignant_id)
            for matiere_id in selected_matieres:
                matiere = Matiere.objects.get(id=matiere_id)
                matiere.enseignants.add(enseignant)
            messages.success(request, 'Affectation réussie !')
        else:
            messages.error(request, "Veuillez sélectionner un enseignant et au moins une matière.")
    context = {
        'form': AffectationForm(),
        'enseignants': enseignants,
        'matieres': matieres,
        'selected_enseignant': selected_enseignant,
        'selected_matieres': selected_matieres,
    }
    return render(request, 'affecter_enseignant.html', context)

#Vue pour affecter un eleve à une classe
def affecter_eleve(request):
    if request.method == 'POST':
        form = AffectationEleveForm(request.POST)
        if form.is_valid():
            utilisateur = form.cleaned_data['eleve']  
            classe = form.cleaned_data['classe']
            try:
                eleve = utilisateur.eleve  
            except Eleve.DoesNotExist:
                messages.error(request, "Cet utilisateur n'est pas un élève.")
                return render(request, 'admin/affecter_eleve.html', {'form': form})

            if eleve.classe is not None:
                messages.error(request, f"L'élève {utilisateur} est déjà affecté à une classe.")
            else:
                eleve.classe = classe
                eleve.save()
                messages.success(request, 'Affectation réussie !')
                return redirect('gestion_utilisateurs')
    else:
        form = AffectationEleveForm()
    return render(request, 'affecter_eleve.html', {'form': form})

