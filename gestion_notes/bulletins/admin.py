from django.contrib import admin
from .models import Bulletin

@admin.register(Bulletin)
class BulletinAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'periode', 'moyenne', 'disponible')
    search_fields = ('eleve__utilisateur__username', 'eleve__utilisateur__first_name', 'eleve__utilisateur__last_name')
    list_filter = ('periode', 'disponible')
