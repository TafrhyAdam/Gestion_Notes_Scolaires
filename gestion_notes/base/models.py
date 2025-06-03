from django.db import models
from django.contrib.auth.models import AbstractUser

# permet à chaque utilisateur d’avoir un role (pour la redirection apres connexion)
class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('enseignant', 'Enseignant'),
        ('eleve', 'Élève'),
        ('parent', 'Parent'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    image = models.ImageField(blank=True, null=True)

    # pour acceder au nom de l utilisateur comme attribut
    @property
    def full_name(self):
        full_name = super().get_full_name()
        return full_name if full_name.strip() else self.username

    def __str__(self):
        return f"{self.username} - {self.role}"

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='base_utilisateur_set',
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='base_utilisateur_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

# Classe
class Classe(models.Model):
    nom = models.CharField(max_length=100)
    matieres = models.ManyToManyField('Matiere', related_name='classes')

    def __str__(self):
        return self.nom



# Matiere
class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    coefficient = models.FloatField()
    enseignants = models.ManyToManyField(
        Utilisateur,
        limit_choices_to={'role': 'enseignant'},
        related_name='matieres',
        blank=True
    )
    def __str__(self):
        return self.nom



# Periode
class Periode(models.Model):
    nom = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin = models.DateField()

    def __str__(self):
        return self.nom



# Eleve
class Eleve(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True)
    parents = models.ManyToManyField(Utilisateur,related_name='enfants',limit_choices_to={'role': 'parent'})


    def __str__(self):
        return f"{self.utilisateur.first_name} {self.utilisateur.last_name}"



# Parent
class Parent(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'parent'})
    def __str__(self):
        return self.utilisateur.username



# Pour graphiques
class Chart(models.Model):
    type = models.CharField(max_length=20)
    donnees = models.JSONField() 
    dateCreation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.dateCreation.strftime('%Y-%m-%d %H:%M')}"



# Evaluation
class Evaluation(models.Model):
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    bareme = models.FloatField()
    coefficient = models.FloatField()
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, related_name='base_evaluations', on_delete=models.CASCADE)
    periode = models.ForeignKey('Periode', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nom} - {self.matiere.nom}"
    
    def calculer_moyenne(self):
        notes = self.notes.all()
    
        if notes.exists():
            total = sum(note.valeur for note in notes)
            return total / notes.count()
            return None



# Note
class Note(models.Model):
    valeur = models.FloatField()
    commentaire = models.TextField(blank=True)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='notes')
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # S'assurer que la note est valide 
        if not (0 <= self.valeur <= 20):
            raise ValueError("La note doit être entre 0 et 20")
        super().save(*args, **kwargs)
        # Recalculer la moyenne apres l'ajout de la note
        self.evaluation.calculer_moyenne()


    
# Bulletin
def get_periode_defaut():
    return Periode.objects.first()  

class Bulletin(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)
    moyenne = models.FloatField()
    fichier_pdf = models.FileField(upload_to="bulletins/")
    periode = models.ForeignKey(Periode, on_delete=models.CASCADE, default=get_periode_defaut)
    disponible = models.BooleanField(default=False)  

    def __str__(self):
        utilisateur = self.eleve.utilisateur
        nom_complet = f"{utilisateur.first_name} {utilisateur.last_name}".strip()
        return f"Bulletin de {nom_complet} ({self.periode.nom})"




# Messages
class Message(models.Model):
    contenu = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    expediteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='messages_recus')

    def __str__(self):
        return f"De {self.expediteur} à {self.destinataire} - {self.date}"



# association eleve classe
class EleveClasse(models.Model):  
    eleve = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'eleve'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('eleve', 'classe')

    def __str__(self):
        return f"{self.eleve.username} - {self.classe.nom}"