from fpdf import FPDF
from docx import Document
import datetime
import os
import re

FONT_REGULAR = "backend/IA/fonts/DejaVuSans.ttf"
FONT_BOLD = "backend/IA/fonts/DejaVuSans-Bold.ttf"
FONT_ITALIC = "backend/IA/fonts/DejaVuSans-Oblique.ttf"

if not os.path.exists(FONT_REGULAR):
    raise FileNotFoundError(f"Police introuvable : {FONT_REGULAR}")

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_font("DejaVu", "", FONT_REGULAR, uni=True)
        if os.path.exists(FONT_BOLD):
            self.add_font("DejaVu", "B", FONT_BOLD, uni=True)
        else:
            self.add_font("DejaVu", "B", FONT_REGULAR, uni=True)
        if os.path.exists(FONT_ITALIC):
            self.add_font("DejaVu", "I", FONT_ITALIC, uni=True)
        else:
            self.add_font("DejaVu", "I", FONT_REGULAR, uni=True)

    def header(self):
        BLUE = (30, 55, 153)
        self.set_draw_color(*BLUE)
        self.set_line_width(0.8)
        self.line(10, 10, 200, 10)
        self.ln(4)

        self.set_text_color(*BLUE)
        self.set_font("DejaVu", "B", 15)
        self.cell(0, 8, "MEETRECAP - Compte rendu automatique", ln=True, align="L")

        self.set_text_color(80, 80, 80)
        self.set_font("DejaVu", "", 11)
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 6, f"Date : {today}          Produit par MeetRecap AI", ln=True)
        self.ln(3)

        self.set_draw_color(*BLUE)
        self.set_line_width(0.8)
        self.line(10, 28, 200, 28)
        self.ln(8)


def is_separator_line(line: str) -> bool:
    #Détecte si une ligne est une ligne de séparation
    return bool(re.match(r'^[\s\u2500-\u257F\-—_]+$', line.strip()))


def clean_lines(text: str) -> list:
    #Nettoie le texte et retourne les lignes sans les séparateurs
    lines = []
    for line in text.split("\n"):
        if line.strip() and not is_separator_line(line):
            lines.append(line)
    return lines


def save_as_pdf(text: str, filename: str = "transcription.pdf"):
    #Sauvegarde le texte en PDF
    #FORCER la suppression de l'ancien fichier s'il existe
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print(f"🗑️  Ancien fichier {filename} supprimé")
        except Exception as e:
            print(f"⚠️  Impossible de supprimer {filename}: {e}")
    
    pdf = PDF()
    pdf.add_page()

    # Parser les sections
    sections_raw = text.split("=====")
    sections = []
    
    for sec in sections_raw:
        sec = sec.strip()
        if not sec:
            continue
        
        # Séparer le nom de section du contenu
        lines = sec.split("\n")
        if len(lines) >= 1:
            section_name = lines[0].strip()
            # Le body
            section_body = "\n".join(lines[1:]).strip()
            
            # Ignorer les sections vides ou qui sont juste des lignes de séparation
            if section_body and not is_separator_line(section_body):
                sections.append((section_name, section_body))
            elif not section_body:
                # Section sans body
                sections.append((section_name, section_body))
    
    print(f"\n📦 {len(sections)} sections valides trouvées")
    
    for section_name, section_body in sections:
        print(f"   → {section_name[:60]}{'...' if len(section_name) > 60 else ''}")
    
    for section_name, section_body in sections:

        # ===== RÉSUMÉ COURT =====
        if section_name == "RÉSUMÉ COURT":
            print(f"📄 Traitement RÉSUMÉ COURT...")
            
            # Titre en BLEU avec ligne
            BLUE = (30, 55, 153)
            pdf.set_text_color(*BLUE)
            pdf.set_font("DejaVu", "B", 13)
            pdf.cell(0, 8, section_name, ln=True)
            pdf.set_text_color(60, 60, 60)
            pdf.set_font("DejaVu", "", 12)
            pdf.cell(0, 5, "────────────────────", ln=True)
            pdf.ln(4)
            
            # Nettoyer TOUTES les lignes de séparation
            text_lines = [line for line in section_body.split("\n") 
                         if line.strip() and not is_separator_line(line)]
            cleaned = "\n".join(text_lines)
            
            print(f"   Paragraphe NOIR: '{cleaned[:80]}...'")
            
            if cleaned:
                pdf.set_text_color(50, 50, 50)
                pdf.set_font("DejaVu", "", 12)
                pdf.multi_cell(0, 7, cleaned)
                pdf.ln(3)

        # ===== COMPTE-RENDU COMPLET =====
        elif section_name == "COMPTE-RENDU COMPLET":
            print(f"📄 Traitement COMPTE-RENDU COMPLET...")
            
            # Titre en BLEU avec ligne
            BLUE = (30, 55, 153)
            pdf.set_text_color(*BLUE)
            pdf.set_font("DejaVu", "B", 13)
            pdf.cell(0, 8, section_name, ln=True)
            pdf.set_text_color(60, 60, 60)
            pdf.set_font("DejaVu", "", 12)
            pdf.cell(0, 5, "────────────────────", ln=True)
            pdf.ln(4)
            
            # Parser ligne par ligne
            current_content = []
            
            for line in section_body.split("\n"):
                if is_separator_line(line):
                    continue
                
                # Détecter les headings Groq (# ...)
                if line.strip().startswith("# "):
                    # Sauvegarder le contenu précédent
                    if current_content:
                        content_text = "\n".join(current_content)
                        pdf.set_text_color(50, 50, 50)
                        pdf.set_font("DejaVu", "", 12)
                        pdf.multi_cell(0, 7, content_text)
                        pdf.ln(3)
                        current_content = []
                    
                    # Afficher le sous-titre en NOIR, italique, SANS ligne
                    subtitle = line.strip()[2:].strip()
                    print(f"   Sous-titre NOIR italique: {subtitle}")
                    pdf.set_text_color(0, 0, 0)  # NOIR
                    pdf.set_font("DejaVu", "I", 13)  # Italique
                    pdf.cell(0, 8, subtitle, ln=True)
                    pdf.ln(2)
                    
                elif line.strip():
                    current_content.append(line)
            
            # Sauvegarder le dernier contenu
            if current_content:
                content_text = "\n".join(current_content)
                pdf.set_text_color(50, 50, 50)
                pdf.set_font("DejaVu", "", 12)
                pdf.multi_cell(0, 7, content_text)
                pdf.ln(3)

        # ===== RÉSUMÉS PAR INTERVENANT =====
        elif section_name == "RÉSUMÉS PAR INTERVENANT":
            print(f"📄 Traitement RÉSUMÉS PAR INTERVENANT...")
            
            # Titre en BLEU avec ligne
            BLUE = (30, 55, 153)
            pdf.set_text_color(*BLUE)
            pdf.set_font("DejaVu", "B", 13)
            pdf.cell(0, 8, section_name, ln=True)
            pdf.set_text_color(60, 60, 60)
            pdf.set_font("DejaVu", "", 12)
            pdf.cell(0, 5, "────────────────────", ln=True)
            pdf.ln(4)
            
            current_speaker = None
            current_text = []
            
            for line in section_body.split("\n"):
                if is_separator_line(line):
                    continue
                
                # Détecter SPEAKER_XX
                if re.match(r'^\s*SPEAKER_\d+\s*$', line.strip()):
                    # Sauvegarder le speaker précédent
                    if current_speaker and current_text:
                        text_content = "\n".join(current_text)
                        pdf.set_text_color(50, 50, 50)
                        pdf.set_font("DejaVu", "", 12)
                        pdf.multi_cell(0, 7, text_content)
                        pdf.ln(3)
                        # Ligne grise
                        pdf.set_text_color(120, 120, 120)
                        pdf.set_font("DejaVu", "", 10)
                        pdf.cell(0, 4, "────────────────────", ln=True)
                        pdf.ln(2)
                    
                    # Nouveau speaker
                    current_speaker = line.strip()
                    print(f"   Speaker NOIR gras: {current_speaker}")
                    pdf.set_text_color(0, 0, 0)  # NOIR
                    pdf.set_font("DejaVu", "B", 12)  # Gras
                    pdf.cell(0, 7, current_speaker, ln=True)
                    pdf.ln(2)
                    current_text = []
                    
                elif line.strip():
                    current_text.append(line)
            
            # Sauvegarder le dernier speaker
            if current_speaker and current_text:
                text_content = "\n".join(current_text)
                pdf.set_text_color(50, 50, 50)
                pdf.set_font("DejaVu", "", 12)
                pdf.multi_cell(0, 7, text_content)
                pdf.ln(3)
                pdf.set_text_color(120, 120, 120)
                pdf.set_font("DejaVu", "", 10)
                pdf.cell(0, 4, "────────────────────", ln=True)
                pdf.ln(2)

        # ===== TRANSCRIPTION AVEC LOCUTEURS ET TIMESTAMPS =====
        elif section_name == "TRANSCRIPTION AVEC LOCUTEURS ET TIMESTAMPS":
            print(f"📄 Traitement TRANSCRIPTION...")
            
            # Titre en BLEU avec ligne
            BLUE = (30, 55, 153)
            pdf.set_text_color(*BLUE)
            pdf.set_font("DejaVu", "B", 13)
            pdf.cell(0, 8, section_name, ln=True)
            pdf.set_text_color(60, 60, 60)
            pdf.set_font("DejaVu", "", 12)
            pdf.cell(0, 5, "────────────────────", ln=True)
            pdf.ln(4)
            
            # Afficher chaque ligne en NOIR
            line_count = 0
            for line in section_body.split("\n"):
                if is_separator_line(line):
                    continue
                
                if line.strip():
                    line_count += 1
                    
                    pdf.set_text_color(0, 0, 0)  # NOIR
                    pdf.set_font("DejaVu", "", 12)
                    pdf.multi_cell(0, 7, line.strip())
                    pdf.ln(2)
                    # Ligne grise après chaque entrée
                    pdf.set_text_color(120, 120, 120)
                    pdf.cell(0, 4, "────────────────────", ln=True)
                    pdf.ln(2)
            
            print(f"   {line_count} lignes de transcription en NOIR")

        # Autres sections
        else:
            BLUE = (30, 55, 153)
            pdf.set_text_color(*BLUE)
            pdf.set_font("DejaVu", "B", 13)
            pdf.cell(0, 8, section_name, ln=True)
            pdf.set_text_color(60, 60, 60)
            pdf.set_font("DejaVu", "", 12)
            pdf.cell(0, 5, "────────────────────", ln=True)
            pdf.ln(4)
            
            cleaned = "\n".join(clean_lines(section_body))
            if cleaned:
                pdf.set_text_color(50, 50, 50)
                pdf.set_font("DejaVu", "", 12)
                pdf.multi_cell(0, 7, cleaned)
                pdf.ln(3)

    pdf.output(filename)
    print(f"✅ PDF sauvegardé sous {filename}")


def save_as_word(text: str, filename: str = "transcription.docx"):
    doc = Document()
    doc.add_heading("MeetRecap - Compte-rendu", level=1)
    doc.add_paragraph(text)
    doc.save(filename)
    print(f"✅ Word sauvegardé sous {filename}")


def save_files(text: str, base_name: str = "transcription"):
    pdf_filename = f"{base_name}.pdf"
    docx_filename = f"{base_name}.docx"
    save_as_pdf(text, pdf_filename)
    save_as_word(text, docx_filename)
    return {"pdf": pdf_filename, "docx": docx_filename}