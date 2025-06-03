from django.db import models
from base.models import Utilisateur, Classe, EleveClasse

# Matiere
class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    coefficient = models.FloatField()
    enseignants = models.ManyToManyField(
        Utilisateur,
        limit_choices_to={'role': 'enseignant'},
        related_name='matieres_affectations',
        blank=True
    )
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='matieres_affectations', null=True, blank=True)
    def __str__(self):
        if self.classe:
            return f"{self.nom} ({self.classe.nom})"
        else:
            return f"{self.nom}"


