from django.shortcuts import render, redirect, get_object_or_404
from .models import Evaluation, Note
from .forms import NoteForm
from django.contrib.auth.decorators import login_required, user_passes_test
from base.models import Eleve, Utilisateur, Classe
from .models import Matiere
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg  
from alertes.models import Alerte  
from django.contrib import messages  
import json


#vue pour saisie de notes

@login_required
def saisie_notes(request):
    utilisateur = request.user
    if utilisateur.role == 'enseignant':
        matieres = Matiere.objects.filter(enseignants=utilisateur)
        evaluations = Evaluation.objects.filter(matiere__in=matieres)
    else:
        evaluations = Evaluation.objects.all()
    classes = Classe.objects.all()
    classe_id = request.GET.get('classe_id')
    evaluation_id = request.GET.get('evaluation_id')

    eleves = []
    notes_dict = {}
    moyenne_classe = None
    moyennes_eleves = {}

    if classe_id and evaluation_id:
        try:
            classe = Classe.objects.get(id=classe_id)
            evaluation = Evaluation.objects.get(id=evaluation_id)
            eleves = Eleve.objects.filter(classe=classe)
        except (Classe.DoesNotExist, Evaluation.DoesNotExist):
            messages.error(request, "Classe ou évaluation introuvable.")
            return redirect('saisie_notes')

        if request.method == 'POST':
            erreurs = []
            for eleve in eleves:
                note_valeur = request.POST.get(f"note_{eleve.id}")
                if note_valeur:
                    try:
                        note_valeur = float(note_valeur)
                        if 0 <= note_valeur <= 20:
                            note_obj, created = Note.objects.update_or_create(
                                eleve=eleve,
                                evaluation=evaluation,
                                defaults={'valeur': note_valeur}
                            )
                            # Creation d alerte
                            seuil = 10.0
                            if note_valeur < seuil:
                                message = f"L'élève {eleve.utilisateur.full_name} a une note faible : {note_valeur:.2f}."
                                # eleve
                                if not Alerte.objects.filter(destinataire=eleve.utilisateur, message=message, vue=False).exists():
                                    Alerte.objects.create(destinataire=eleve.utilisateur, message=message)
                                # Parents
                                for parent in eleve.parents.all():
                                    if not Alerte.objects.filter(destinataire=parent, message=message, vue=False).exists():
                                        Alerte.objects.create(destinataire=parent, message=message)
                                # Enseignants de la matière 
                                for enseignant in evaluation.matiere.enseignants.all():
                                    if not Alerte.objects.filter(destinataire=enseignant, message=message, vue=False).exists():
                                        Alerte.objects.create(destinataire=enseignant, message=message)
                                # Admins
                                admins = Utilisateur.objects.filter(role__iexact='admin')
                                for admin in admins:
                                    if not Alerte.objects.filter(destinataire=admin, message=message, vue=False).exists():
                                        Alerte.objects.create(destinataire=admin, message=message)
                        else:
                            erreurs.append(f"La note pour {eleve.utilisateur.get_full_name()} doit être entre 0 et 20.")
                    except ValueError:
                        erreurs.append(f"Note invalide pour {eleve.utilisateur.get_full_name()}.")
            if erreurs:
                for erreur in erreurs:
                    messages.error(request, erreur)
            else:
                messages.success(request, "Les notes ont été enregistrées avec succès.")
                return redirect(f"{request.path}?classe_id={classe_id}&evaluation_id={evaluation_id}")

        for eleve in eleves:
            note = Note.objects.filter(eleve=eleve, evaluation=evaluation).first()
            if note:
                notes_dict[eleve.id] = note.valeur

        # Moyenne de la classe pour l'evaluation selectionnee
        moyenne = Note.objects.filter(evaluation=evaluation, eleve__classe=classe).aggregate(Avg('valeur'))['valeur__avg']
        moyenne_classe = round(moyenne, 2) if moyenne is not None else None

        # Moyenne individuelle de chaque eleve 
        for eleve in eleves:
            moyenne_eleve = Note.objects.filter(eleve=eleve).aggregate(Avg('valeur'))['valeur__avg']
            moyennes_eleves[eleve.id] = round(moyenne_eleve, 2) if moyenne_eleve is not None else None

    return render(request, 'saisie_notes.html', {
        'classes': classes,
        'evaluations': evaluations,
        'classe_id': int(classe_id) if classe_id else None,
        'evaluation_id': int(evaluation_id) if evaluation_id else None,
        'eleves': eleves,
        'notes_dict': notes_dict,
        'moyenne_classe': moyenne_classe,
        'moyennes_eleves': moyennes_eleves,
    })





# Vue pour consulter les notes
@login_required
def consulter_notes(request):
    utilisateur = request.user
    est_parent = False

    # Cas Élève
    if utilisateur.role == 'eleve':
        try:
            eleve = Eleve.objects.get(utilisateur=utilisateur)
            notes_qs = Note.objects.filter(eleve=eleve).select_related('evaluation__matiere')

            notes_data = [
                {
                    'matiere': note.evaluation.matiere.nom,
                    'evaluation': note.evaluation.nom,
                    'note': float(note.valeur)
            }
            for note in notes_qs
            ]
            notes_data_json = json.dumps(notes_data, cls=DjangoJSONEncoder)

        except Eleve.DoesNotExist:
            notes_qs = []
            notes_data = []

        return render(request, 'consulter_notes.html', {
            'notes': notes_qs,
            'est_parent': est_parent,
            'notes_data_json': notes_data_json
        })


    # Cas Parent
    elif utilisateur.role == 'parent':
        est_parent = True
        enfants = Eleve.objects.filter(parents=utilisateur)
        enfants_notes = []
        enfants_notes_data = []

        for eleve in enfants:
            notes_qs = Note.objects.filter(eleve=eleve).select_related('evaluation__matiere')
            enfants_notes.append({
                'eleve': eleve,
                'notes': notes_qs,
            })

            # Donnees graphiques pour l enfant
            notes_data = []
            for note in notes_qs:
                notes_data.append({
                    'matiere': note.evaluation.matiere.nom,
                    'evaluation': note.evaluation.nom,
                    'note': float(note.valeur),
                })

            enfants_notes_data.append({
                'eleve_id': eleve.id,
                'eleve_nom': str(eleve),
                'notes_data': notes_data,
            })

        return render(request, 'consulter_notes_parent.html', {
            'enfants_notes': enfants_notes,
            'enfants_notes_data_json': json.dumps(enfants_notes_data, cls=DjangoJSONEncoder),
            'est_parent': est_parent,
        })

    # Cas par defaut
    else:
        return render(request, 'consulter_notes.html', {
            'notes': [],
            'notes_data_json': '[]',
            'est_parent': False,
        })



# vue pour affciher graphiques
def is_enseignant(user):
    return user.is_authenticated and user.role == 'enseignant'


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


@login_required
@user_passes_test(is_enseignant)
def enseignant_stats(request):
    utilisateur = request.user
    matieres = Matiere.objects.filter(enseignants=utilisateur)
    classes = Classe.objects.filter(matieres_evaluations__in=matieres).distinct()
    stats = []

    for classe in classes:
        eleves = Eleve.objects.filter(classe=classe)
        moyennes = []
        for eleve in eleves:
            notes = Note.objects.filter(eleve=eleve)
            if notes.exists():
                moyenne = sum(note.valeur for note in notes) / notes.count()
                moyennes.append(moyenne)
        moyenne_classe = round(sum(moyennes) / len(moyennes), 2) if moyennes else None
        if moyenne_classe is not None:
            stats.append({
                'classe': classe.nom,
                'moyenne': moyenne_classe,
                'effectif': eleves.count(),
            })

    stats_json = json.dumps(stats, cls=DjangoJSONEncoder)

    return render(request, 'enseignant_stats.html', {
        'stats': stats,
        'classes': classes,
        'stats_json': stats_json,
    })

@login_required
@user_passes_test(is_admin)
def admin_stats(request):
    nb_eleves = Eleve.objects.count()
    nb_enseignants = Utilisateur.objects.filter(role='enseignant').count()
    nb_classes = Classe.objects.count()
    nb_parents = Utilisateur.objects.filter(role='parent').count()
    notes = Note.objects.all()
    moyenne_generale = round(notes.aggregate(Avg('valeur'))['valeur__avg'], 2) if notes.exists() else None

    repartition_classes = []
    for classe in Classe.objects.all():
        effectif = Eleve.objects.filter(classe=classe).count()
        repartition_classes.append({'classe': classe.nom, 'effectif': effectif})

    moyennes_classes = []
    for classe in Classe.objects.all():
        eleves = Eleve.objects.filter(classe=classe)
        moyennes = []
        for eleve in eleves:
            notes_eleve = Note.objects.filter(eleve=eleve)
            if notes_eleve.exists():
                moy = sum(note.valeur for note in notes_eleve) / notes_eleve.count()
                moyennes.append(moy)
        moyenne_classe = round(sum(moyennes) / len(moyennes), 2) if moyennes else 0 
        moyennes_classes.append({'classe': classe.nom, 'moyenne': moyenne_classe})

    moyennes_classes_json = json.dumps(moyennes_classes, cls=DjangoJSONEncoder)

    return render(request, 'admin_stats.html', {
        'nb_eleves': nb_eleves,
        'nb_enseignants': nb_enseignants,
        'nb_classes': nb_classes,
        'nb_parents': nb_parents,
        'moyenne_generale': moyenne_generale,
        'repartition_classes': repartition_classes,
        'moyennes_classes': moyennes_classes,
        'moyennes_classes_json': moyennes_classes_json,  
    })
