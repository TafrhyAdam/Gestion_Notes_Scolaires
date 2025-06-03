from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404
from alertes.models import Alerte, Utilisateur, Eleve
from evaluations.models import Matiere
from collections import defaultdict 
from django.contrib.auth.hashers import make_password
from base.models import Classe  


# Vue de connexion
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirection selon le rôle
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'enseignant':
                    return redirect('enseignant_dashboard')
                elif user.role == 'eleve':
                    return redirect('eleve_dashboard')
                elif user.role == 'parent':
                    return redirect('parent_dashboard')
    else:
        form = LoginForm()
    return render(request, 'utilisateurs/login.html', {'form': form})


#admin
def is_admin(user):
    return user.role.strip().lower() == 'admin' 

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    alertes = Alerte.objects.filter(destinataire=request.user, vue=False).order_by('-date')
    return render(request, 'utilisateurs/admin_dashboard.html', {'alertes': alertes})



#enseignant
def is_enseignant(user):
    return user.role == 'enseignant'

@login_required
@user_passes_test(is_enseignant)
def enseignant_dashboard(request):
    utilisateur = request.user
    if utilisateur.role != 'enseignant':
        return redirect('accueil')  # ou afficher un message d'erreur

    alertes = Alerte.objects.filter(destinataire=utilisateur, vue=False).order_by('-id')


    context = {
        'alertes': alertes,
    }
    return render(request, 'utilisateurs/enseignant_dashboard.html', context)



#eleve
def is_eleve(user):
    return user.role == 'eleve'

@login_required
@user_passes_test(is_eleve)
def eleve_dashboard(request):
    alertes = Alerte.objects.filter(destinataire=request.user, vue=False).order_by('-date')
    return render(request, 'utilisateurs/eleve_dashboard.html', {'alertes': alertes})



#parent
def is_parent(user):
    return user.role == 'parent'

@login_required
@user_passes_test(is_parent)
def parent_dashboard(request):
    alertes = Alerte.objects.filter(destinataire=request.user, vue=False).order_by('-date')
    return render(request, 'utilisateurs/parent_dashboard.html', {'alertes': alertes})


#fct test
def est_admin(user):
    return user.is_authenticated and user.role == 'administrateur'



# Vue pour la gestion des utilisateurs
@login_required
@user_passes_test(lambda u: u.role == 'admin')
def gestion_utilisateurs(request):
    # Enseignants avec et sans matieres
    enseignants = Utilisateur.objects.filter(role='enseignant').annotate(nb_matieres=Count('matieres'))
    enseignants_avec_matiere = enseignants.filter(nb_matieres__gt=0)
    enseignants_sans_matiere = enseignants.filter(nb_matieres=0)

    # Eleves avec leurs parents et classes
    eleves = Eleve.objects.select_related('utilisateur', 'classe')
    classes = Classe.objects.all()

    # Eleves par classe
    eleves_par_classe = {classe: eleves.filter(classe=classe) for classe in classes}

    # Eleves sans classe
    eleves_sans_classe = eleves.filter(classe__isnull=True)

    # Regrouper les parents selon la classe de leurs enfants avec les enfants
    parents = Utilisateur.objects.filter(role='parent').distinct()

    parents_par_classe = defaultdict(list)
    parents_sans_classe = []

    for parent in parents:
        enfants = Eleve.objects.filter(parents=parent).select_related('utilisateur', 'classe')
        classes_du_parent = set()

        for enfant in enfants:
            if enfant.classe:
                classes_du_parent.add(enfant.classe)

        if classes_du_parent:
            for classe in classes_du_parent:
                parents_par_classe[classe].append({'parent': parent, 'enfants': enfants})
        else:
            parents_sans_classe.append({'parent': parent, 'enfants': enfants})

    context = {
        'enseignants_avec_matiere': enseignants_avec_matiere,
        'enseignants_sans_matiere': enseignants_sans_matiere,
        'eleves_par_classe': eleves_par_classe,
        'eleves_sans_classe': eleves_sans_classe,
        'parents_par_classe': dict(parents_par_classe),
        'parents_sans_classe': parents_sans_classe,
    }
    return render(request, 'utilisateurs/gestion_utilisateurs.html', context)


# Vue de creation d'utilisateur
@login_required
@user_passes_test(lambda u: u.role == 'admin')
def creer_utilisateur(request):
    classes = Classe.objects.all()
    matieres = Matiere.objects.all()
    eleves = Eleve.objects.select_related('utilisateur', 'classe')

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']

        utilisateur = Utilisateur.objects.create(
            username=username,
            email=email,
            role=role,
            password=make_password(password)
        )

        if role == 'eleve':
            Eleve.objects.create(utilisateur=utilisateur)
        elif role == 'enseignant':
            matiere_ids = request.POST.getlist('matiere_ids')
            if not matiere_ids or not utilisateur:
                messages.error(request, "Veuillez sélectionner un enseignant et au moins une matière.")
                return render(request, 'utilisateurs/creer_utilisateurs.html', {
                    'classes': classes,
                    'matieres': matieres,
                    'eleves': eleves,
                    'enfants_selectionnes': []
                })
            for matiere_id in matiere_ids:
                if matiere_id:
                    try:
                        matiere = Matiere.objects.get(id=matiere_id)
                        matiere.enseignants.add(utilisateur)
                    except Matiere.DoesNotExist:
                        continue
        elif role == 'parent':
            Parent.objects.create(utilisateur=utilisateur)
            enfants_ids = request.POST.getlist('enfants')
            for enfant_id in enfants_ids:
                eleve = Eleve.objects.get(id=enfant_id)
                eleve.parents.add(utilisateur)
                eleve.save()

        messages.success(request, "Utilisateur créé avec succès.")
        return redirect('gestion_utilisateurs')

    return render(request, 'utilisateurs/creer_utilisateurs.html', {
        'classes': classes,
        'matieres': matieres,
        'eleves': eleves,
        'enfants_selectionnes': []
    })



# Vue de modification d utilisateur
@login_required
@user_passes_test(lambda u: u.role == 'admin')
def modifier_utilisateur(request, utilisateur_id):
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    classes = Classe.objects.all()
    matieres = Matiere.objects.all()
    eleves = Eleve.objects.select_related('utilisateur', 'classe')

    classe_id = None
    matiere_ids = []
    enfants_selectionnes = []

    if utilisateur.role == "eleve" and hasattr(utilisateur, 'eleve'):
        if utilisateur.eleve.classe:
            classe_id = utilisateur.eleve.classe.id
        else:
            classe_id = None

    elif utilisateur.role == "enseignant":
        matiere_ids = list(utilisateur.matieres.values_list('id', flat=True))

    elif utilisateur.role == "parent":
        enfants_selectionnes = Eleve.objects.filter(parents=utilisateur).values_list('id', flat=True)

    if request.method == 'POST':
        nouveau_role = request.POST['role']
        ancien_role = utilisateur.role

        utilisateur.username = request.POST['username']
        utilisateur.email = request.POST['email']
        utilisateur.role = nouveau_role
        if request.POST.get('password'):
            utilisateur.password = make_password(request.POST['password'])
        utilisateur.save()

        if ancien_role != nouveau_role:
            if ancien_role == 'eleve' and hasattr(utilisateur, 'eleve'):
                utilisateur.eleve.delete()

            if ancien_role == 'enseignant':
                for matiere in Matiere.objects.filter(enseignants=utilisateur):
                    matiere.enseignants.remove(utilisateur)

            if ancien_role == 'parent':
                for eleve in Eleve.objects.filter(parents=utilisateur):
                    eleve.parents.remove(utilisateur)

        if nouveau_role == 'eleve':
            classe_id_post = request.POST.get('classe_id')
            if classe_id_post:
                classe = Classe.objects.get(id=classe_id_post)
                eleve_obj, created = Eleve.objects.get_or_create(utilisateur=utilisateur, defaults={'classe': classe})
                if not created:
                    eleve_obj.classe = classe
                    eleve_obj.save()

        elif nouveau_role == 'enseignant':
            nouvelle_matiere_ids = request.POST.getlist('matiere_ids')
            for matiere in Matiere.objects.filter(enseignants=utilisateur):
                matiere.enseignants.remove(utilisateur)
            for matiere_id in nouvelle_matiere_ids:
                try:
                    matiere = Matiere.objects.get(id=matiere_id)
                    matiere.enseignants.add(utilisateur)
                except Matiere.DoesNotExist:
                    pass

        elif nouveau_role == 'parent':
            parent_obj, created = Parent.objects.get_or_create(utilisateur=utilisateur)
            enfants_ids = request.POST.getlist('enfants')
            for eleve in Eleve.objects.filter(parents=utilisateur):
                eleve.parents.remove(utilisateur)
            for enfant_id in enfants_ids:
                try:
                    eleve = Eleve.objects.get(id=enfant_id)
                    eleve.parents.add(utilisateur)
                except Eleve.DoesNotExist:
                    pass

        messages.success(request, "Utilisateur modifié.")
        return redirect('gestion_utilisateurs')

    return render(request, 'utilisateurs/modifier_utilisateur.html', {
        'utilisateur': utilisateur,
        'classes': classes,
        'matieres': matieres,
        'eleves': eleves,
        'classe_id': classe_id,
        'matiere_ids': matiere_ids,
        'enfants_selectionnes': enfants_selectionnes
    })

# Suppression d'utilisateur
@login_required
@user_passes_test(lambda u: u.role == 'admin')
def supprimer_utilisateur(request, utilisateur_id):
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    utilisateur.delete()
    messages.success(request, "Utilisateur supprimé.")
    return redirect('gestion_utilisateurs')