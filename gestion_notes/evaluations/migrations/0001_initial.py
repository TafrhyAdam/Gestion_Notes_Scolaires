# Generated by Django 5.2.1 on 2025-06-03 14:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Matiere',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('coefficient', models.FloatField()),
                ('classe', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='matieres_evaluations', to='base.classe')),
                ('enseignants', models.ManyToManyField(blank=True, limit_choices_to={'role': 'enseignant'}, related_name='matieres_evaluations', to='base.utilisateur')),
            ],
        ),
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=100)),
                ('bareme', models.FloatField()),
                ('coefficient', models.FloatField()),
                ('classe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations_evaluations', to='base.classe')),
                ('periode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations_evaluations', to='base.periode')),
                ('matiere', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='evaluations.matiere')),
            ],
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valeur', models.FloatField()),
                ('commentaire', models.TextField(blank=True)),
                ('eleve', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes_evaluations', to='base.eleve')),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='evaluations.evaluation')),
            ],
        ),
    ]
