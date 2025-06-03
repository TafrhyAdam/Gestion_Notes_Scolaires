from django.db import models
from base.models import Utilisateur, Classe, Eleve


class Alerte(models.Model):
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, null=True, blank=True)
    destinataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='alertes', null=True, blank=True, limit_choices_to={'role__in': ['enseignant', 'parent', 'eleve']})
    vue = models.BooleanField(default=False)

    def __str__(self):
        destinataire_str = self.destinataire.username if self.destinataire else "Inconnu"
        return f"Alerte pour {destinataire_str} - {self.date.strftime('%Y-%m-%d %H:%M')}"

