from django.db import models
from base.models import Classe, Utilisateur, Eleve, Periode

#evaluation 
class Evaluation(models.Model):
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    bareme = models.FloatField()
    coefficient = models.FloatField()
    matiere = models.ForeignKey('Matiere', on_delete=models.CASCADE, related_name='evaluations')
    classe = models.ForeignKey(Classe, related_name='evaluations_evaluations', on_delete=models.CASCADE)
    periode = models.ForeignKey(Periode, on_delete=models.CASCADE, related_name='evaluations_evaluations')

    def __str__(self):
        return f"{self.nom} - {self.matiere.nom}"

    def calculer_moyenne(self):
        notes = self.notes.all()
        if notes.exists():
            total = sum(note.valeur for note in notes)
            return total / notes.count()
        return None


#note
class Note(models.Model):
    valeur = models.FloatField()
    commentaire = models.TextField(blank=True)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='notes')
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='notes_evaluations')

    def save(self, *args, **kwargs):
        if not (0 <= self.valeur <= 20):
            raise ValueError("La note doit être entre 0 et 20")
        super().save(*args, **kwargs)
        self.evaluation.calculer_moyenne()


# Matiere
class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    coefficient = models.FloatField()
    enseignants = models.ManyToManyField(
        Utilisateur,
        limit_choices_to={'role': 'enseignant'},
        related_name='matieres_evaluations',
        blank=True
    )
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='matieres_evaluations', null=True, blank=True)
    def __str__(self):
        if self.classe:
            return f"{self.nom} ({self.classe.nom})"
        else:
            return f"{self.nom}"

