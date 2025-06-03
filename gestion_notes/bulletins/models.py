from django.db import models
from base.models import Eleve, Periode


class Bulletin(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='bulletins')
    moyenne = models.FloatField()
    fichier_pdf = models.FileField(upload_to="bulletins/")
    periode = models.ForeignKey(Periode, on_delete=models.CASCADE, related_name='bulletins')
    disponible = models.BooleanField(default=False)

    def __str__(self):
        utilisateur = self.eleve.utilisateur
        nom_complet = f"{utilisateur.first_name} {utilisateur.last_name}".strip()
        return f"Bulletin de {nom_complet} ({self.periode.nom})"
