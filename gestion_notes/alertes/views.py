from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from base.models import Utilisateur, Eleve, Note
from .models import Alerte


#admin
def is_admin(user):
    return user.role.strip().lower() == 'admin' 

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    alertes = Alerte.objects.filter(destinataire=request.user, vue=False).order_by('-date')
    return render(request, 'dashboards/admin_dashboard.html', {'alertes': alertes})



#enseignant
def is_enseignant(user):
    return user.role == 'enseignant'

@login_required
@user_passes_test(is_enseignant)
def enseignant_dashboard(request):
    utilisateur = request.user
    if utilisateur.role != 'enseignant':
        return redirect('accueil')  

    alertes = Alerte.objects.filter(destinataire=utilisateur, vue=False).order_by('-id')


    context = {
        'alertes': alertes,
    }
    return render(request, 'dashboards/enseignant_dashboard.html', context)



#eleve
def is_eleve(user):
    return user.role == 'eleve'

@login_required
@user_passes_test(is_eleve)
def eleve_dashboard(request):
    alertes = Alerte.objects.filter(destinataire=request.user, vue=False).order_by('-date')
    return render(request, 'dashboards/eleve_dashboard.html', {'alertes': alertes})



#parent
def is_parent(user):
    return user.role == 'parent'

@login_required
@user_passes_test(is_parent)
def parent_dashboard(request):
    alertes = Alerte.objects.filter(destinataire=request.user, vue=False).order_by('-date')
    return render(request, 'dashboards/parent_dashboard.html', {'alertes': alertes})


#fonction test
def est_admin(user):
    return user.is_authenticated and user.role == 'administrateur'



# Vue pour creer les alertes pour les notes faibles <10
def creer_alertes_resultats_faibles(seuil=10):
    admins = Utilisateur.objects.filter(role__iexact='admin')
    alertes_creees = []

    eleves = Eleve.objects.select_related('classe').prefetch_related(
        Prefetch('note_set', queryset=Note.objects.select_related('evaluation__matiere')),
        'parents',
    )

    for eleve in eleves:
        notes = eleve.note_set.all()
        if notes.exists():
            moyenne = sum(note.valeur for note in notes) / notes.count()

            if moyenne < seuil:
                notes_faibles = [note for note in notes if note.valeur < seuil]

                for note in notes_faibles:
                    message = f"L'élève {eleve.utilisateur.full_name} a une note faible : {note.valeur:.2f}."
                    
                    # Eleve
                    if not Alerte.objects.filter(destinataire=eleve.utilisateur, message=message, vue=False).exists():
                        alertes_creees.append(
                            Alerte.objects.create(
                                eleve=eleve,
                                destinataire=eleve.utilisateur,
                                message=message
                            )
                        )

                    # Parent
                    for parent in eleve.parents.all():
                        if not Alerte.objects.filter(destinataire=parent, message=message, vue=False).exists():
                            alertes_creees.append(
                                Alerte.objects.create(
                                    eleve=eleve,
                                    destinataire=parent,
                                    message=message
                                )
                            )
                    #Enseignant de la matiere
                    enseignant = note.evaluation.matiere.enseignant
                    if enseignant and not Alerte.objects.filter(destinataire=enseignant, message=message, vue=False).exists():
                        alertes_creees.append(
                            Alerte.objects.create(
                                eleve=eleve,
                                destinataire=enseignant,
                                message=message
                            )
                        )
                    # Admin
                    for admin in admins:
                        if not Alerte.objects.filter(destinataire=admin, message=message, vue=False).exists():
                            alertes_creees.append(
                                Alerte.objects.create(
                                    eleve=eleve,
                                    destinataire=admin,
                                    message=message
                                )
                            )

    return alertes_creees


# Vue pour pouvoir marquer une alerte comme lue
@login_required
def marquer_alerte_lue(request, alerte_id):
    alerte = get_object_or_404(Alerte, id=alerte_id, destinataire=request.user)
    alerte.vue = True
    alerte.save()
    

    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'enseignant':
        return redirect('enseignant_dashboard')
    elif request.user.role == 'eleve':
        return redirect('eleve_dashboard')
    elif request.user.role == 'parent':
        return redirect('parent_dashboard')
    else:
        return redirect('login')