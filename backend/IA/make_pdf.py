import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap

def make_pdf(output_path, title, summary, transcription):
    """
    Génère un fichier PDF contenant le résumé et la transcription.

  """

    #  Conversion du Path en chaîne 
    output_path = str(output_path)

    # Vérifier le dossier de sortie
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Créer le document PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Titre principal
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 80, title)

    # Section Résumé
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 120, "Résumé :")
    c.setFont("Helvetica", 12)
    y = height - 140

    # Ajouter le résumé avec retour à la ligne automatique
    for line in wrap(summary, 100):
        c.drawString(50, y, line)
        y -= 16

    # Ajouter une séparation
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Transcription complète :")
    y -= 20
    c.setFont("Helvetica", 11)

    # Ajouter la transcription 
    for line in wrap(transcription, 100):
        if y < 60:  # fin de page
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)
        c.drawString(50, y, line)
        y -= 14

    # ✅ Sauvegarde du fichier
    c.save()

    print(f"✅ PDF généré avec succès : {output_path}")
