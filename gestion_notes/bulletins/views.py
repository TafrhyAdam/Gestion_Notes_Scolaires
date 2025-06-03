from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib import messages
from datetime import date
from base.models import Classe, Eleve, Parent, Periode, Note
from .models import Bulletin
from .utils import generer_bulletin_pdf_et_enregistrer


from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


# Vue pour afficher bulletins et resultats

@login_required
@user_passes_test(is_admin)
def page_resultats_bulletins(request):
    classes = Classe.objects.all()
    classe_id = request.GET.get('classe_id')
    eleves = []
    bulletins = Bulletin.objects.all().select_related('eleve', 'periode')
    if classe_id:
        eleves = Eleve.objects.filter(classe_id=classe_id).select_related('utilisateur')
        bulletins = bulletins.filter(eleve__classe_id=classe_id)
    # Optionnel : filtrer par période si vous souhaitez n'afficher que la période courante
    # periode = Periode.objects.filter(date_debut__lte=date.today(), date_fin__gte=date.today()).first()
    # if periode:
    #     bulletins = bulletins.filter(periode=periode)
    fichiers = []
    for bulletin in bulletins:
        if bulletin.fichier_pdf:
            fichiers.append({
                'url': bulletin.fichier_pdf.url,
                'nom': bulletin.fichier_pdf.name.split('/')[-1]
            })
    return render(request, 'bulletins_resultats.html', {
        'classes': classes,
        'eleves': eleves,
        'classe_id': classe_id,
        'bulletins': bulletins,  # <-- minuscule
        'fichiers': fichiers,
    })


# Vue pour generer les bulletins
@login_required
@user_passes_test(is_admin)
@require_POST
def generer_bulletins_multiple(request):
    
    eleves_ids = request.POST.getlist('eleves')

    if not eleves_ids:
        messages.warning(request, "Veuillez sélectionner au moins un élève.")
        return redirect(request.META.get('HTTP_REFERER', 'page_resultats_bulletins'))

    eleves = Eleve.objects.filter(id__in=eleves_ids).select_related('utilisateur', 'classe')

    bulletins_data = []
    for eleve in eleves:
        notes = Note.objects.filter(eleve=eleve).select_related('evaluation', 'evaluation__matiere')
        classe = eleve.classe
        bulletins_data.append({
            'eleve': eleve,
            'notes': notes,
            'classe': classe,
        })

    periode = Periode.objects.filter(date_debut__lte=date.today(), date_fin__gte=date.today()).first()
    if not periode:
        periode = Periode.objects.first()

    bulletins = generer_bulletin_pdf_et_enregistrer(bulletins_data, periode=periode)

    messages.success(request, f"Bulletins générés et enregistrés pour {len(bulletins)} élève(s).")
    return redirect(request.META.get('HTTP_REFERER', 'page_resultats_bulletins'))


# Vue pour que l'eleve voie ses bulletins 
@login_required
@login_required
def bulletin_eleve(request):
    try:
        eleve = request.user.eleve
    except Eleve.DoesNotExist:
        messages.error(request, "Vous n'êtes pas autorisé à voir un bulletin.")
        return redirect('accueil')

    bulletins = Bulletin.objects.filter(eleve=eleve, disponible=True).select_related('periode').order_by('-periode__date_debut')

    return render(request, 'bulletin_eleve.html', {
        'eleve': eleve,
        'bulletins': bulletins,
    })



# Vue pour que le parent voie les bulletins de ses enfants
@login_required
def bulletins_parent(request):
    try:
        parent = request.user.parent
    except Parent.DoesNotExist:
        messages.error(request, "Vous n'êtes pas autorisé à voir des bulletins.")
        return redirect('accueil')

    enfants = Eleve.objects.filter(parents=parent.utilisateur)
    bulletins_par_enfant = {}
    for eleve in enfants:
        bulletins = Bulletin.objects.filter(eleve=eleve, disponible=True).select_related('periode').order_by('-periode__date_debut')
        bulletins_par_enfant[eleve] = bulletins

    return render(request, 'bulletins_parent.html', {
        'bulletins_par_enfant': bulletins_par_enfant
    })


# Vue pour rendre les bulletins dispo ou indispo
@login_required
@user_passes_test(is_admin)
@require_POST
def rendre_bulletins_disponibles(request):
    ids = request.POST.getlist('bulletin_ids')
    action = request.POST.get('action')
    if action == "disponible":
        Bulletin.objects.filter(id__in=ids).update(disponible=True)
        messages.success(request, "Les bulletins sélectionnés sont maintenant disponibles pour les élèves et parents.")
    elif action == "indisponible":
        Bulletin.objects.filter(id__in=ids).update(disponible=False)
        messages.success(request, "Les bulletins sélectionnés sont maintenant indisponibles pour les élèves et parents.")
    return redirect('page_resultats_bulletins')


# Vue pour supprimer un bulletin
@login_required
@user_passes_test(is_admin)
def supprimer_bulletin(request, bulletin_id):
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    if bulletin.fichier_pdf:
        bulletin.fichier_pdf.delete(save=False)
    bulletin.delete()
    messages.success(request, "Le bulletin a été supprimé.")
    return redirect('page_resultats_bulletins')