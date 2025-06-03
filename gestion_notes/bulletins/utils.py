import os
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from django.conf import settings
from .models import Bulletin
from reportlab.pdfgen import canvas
from django.core.files import File
from reportlab.lib.enums import TA_CENTER

def definir_meta_infos_default(canvas, doc):
    canvas.setTitle("Bulletin scolaire")


def generer_bulletin_pdf_et_enregistrer(bulletins_data, definir_meta_infos=None, periode=None):

    fichiers = []
    dossier = os.path.join(settings.MEDIA_ROOT, 'bulletins')
    os.makedirs(dossier, exist_ok=True)

    for data in bulletins_data:
        eleve = data['eleve']
        utilisateur = eleve.utilisateur  # acces au cpt utilisateur

        # Informations a partir du modele Utilisateur
        username = utilisateur.username
        nom_complet = f"{utilisateur.first_name} {utilisateur.last_name}".strip()

        nom_fichier = f"{username}_bulletin.pdf"
        chemin = os.path.join(dossier, nom_fichier)

        doc = SimpleDocTemplate(chemin, pagesize=A4)
        styles = getSampleStyleSheet()
        style_title = styles['Title']
        style_normal = styles['Normal']
        style_heading = styles['Heading2']


        style_title_custom = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=22,
            alignment=TA_CENTER,
            spaceAfter=16,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        )
        style_label = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=10,
        )
        style_table_header = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=13,
            alignment=TA_CENTER,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )
        style_table_cell = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
        )
        style_moyenne = ParagraphStyle(
            'Moyenne',
            parent=styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceBefore=18,
            spaceAfter=18,
        )

        elements = []

        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'LogoEcole.png')
        if os.path.exists(logo_path):
            img = Image(logo_path, width=3.5*cm, height=3.5*cm)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.2*cm))

        elements.append(Paragraph(f"<b>Bulletin de : {nom_complet or username}</b>", style_title_custom))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph(f"Classe : {data['classe']}", style_label))
        elements.append(Spacer(1, 0.2*cm))

        # Regrouper les notes par matiere et calculer la moyenne de chaque matiere
        matieres_dict = {}
        for note in data['notes']:
            matiere = getattr(note.evaluation, 'matiere', None)
            if matiere:
                matiere_nom = str(matiere)
                coeff = getattr(note.evaluation, 'coefficient', 1)
                if matiere_nom not in matieres_dict:
                    matieres_dict[matiere_nom] = {'total': 0, 'count': 0, 'coeff': coeff}
                matieres_dict[matiere_nom]['total'] += note.valeur
                matieres_dict[matiere_nom]['count'] += 1
                matieres_dict[matiere_nom]['coeff'] = coeff 

        table_data = [
            [
                Paragraph("Matière", style_table_header),
                Paragraph("Moyenne", style_table_header),
                Paragraph("Coefficient", style_table_header)
            ]
        ]

        total_notes = 0
        total_coeff = 0
        for matiere_nom, infos in matieres_dict.items():
            moyenne_matiere = infos['total'] / infos['count'] if infos['count'] else 0
            coeff = infos['coeff']
            table_data.append([
                Paragraph(matiere_nom, style_table_cell),
                Paragraph(f"{moyenne_matiere:.2f}", style_table_cell),
                Paragraph(f"{coeff:.1f}", style_table_cell)
            ])
            total_notes += moyenne_matiere * coeff
            total_coeff += coeff

        moyenne = (total_notes / total_coeff) if total_coeff else 0

        table_style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#666666")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 13),
            ('FONTSIZE', (0,1), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ])

        table = Table(table_data, colWidths=[7*cm, 3.5*cm, 3.5*cm])
        table.hAlign = 'CENTER'
        table.setStyle(table_style)
        elements.append(table)

        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Moyenne générale : <b>{moyenne:.2f}</b>", style_moyenne))
        elements.append(Spacer(1, 1*cm))

        elements.append(Paragraph("Signature du responsable :", style_label))
        elements.append(Spacer(1, 1*cm))

        doc.build(elements, onFirstPage=definir_meta_infos or definir_meta_infos_default)
        fichiers.append(chemin)


        # Calcul de la moyenne generale
        moyenne = (total_notes / total_coeff) if total_coeff else 0

        # Recuperer ou creer le bulletin pour l'eleve et la periode
        bulletin_obj, created = Bulletin.objects.get_or_create(
            eleve=eleve,
            periode=periode,
            defaults={'moyenne': moyenne}
        )
        # Si le bulletin existe deja, on met à jour la moyenne
        if not created:
            bulletin_obj.moyenne = moyenne

        # Supprimer l'ancien PDF si besoin
        if bulletin_obj.fichier_pdf:
            bulletin_obj.fichier_pdf.delete(save=False)

        # Associer le nouveau PDF
        with open(chemin, 'rb') as f:
            bulletin_obj.fichier_pdf.save(nom_fichier, File(f), save=True)

    return fichiers